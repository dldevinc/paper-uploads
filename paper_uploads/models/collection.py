import datetime
import posixpath
import warnings
from collections import OrderedDict
from typing import Any, ClassVar, Dict, Iterable, Optional, Type

import magic
from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.finders import find
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core import checks
from django.core.files import File
from django.core.files.storage import Storage
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.fields.files import FieldFile
from django.db.models.functions import Coalesce
from django.template import loader
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from polymorphic.base import PolymorphicModelBase
from polymorphic.models import PolymorphicModel

from .. import exceptions
from ..conf import FILE_ICON_DEFAULT, FILE_ICON_OVERRIDES, IMAGE_ITEM_VARIATIONS, settings
from ..helpers import (
    _get_item_types,
    _set_item_types,
    build_variations,
    iterate_variation_names,
)
from ..storage import default_storage
from ..utils import cached_method
from ..variations import PaperVariation
from .base import (
    FileFieldResource,
    NoPermissionsMetaBase,
    Resource,
    ResourceBaseMeta,
    SVGFileResourceMixin,
    VersatileImageResourceMixin,
)
from .fields import CollectionItem
from .fields.base import DynamicStorageFileField
from .fields.collection import ContentItemRelation
from .image import VariationalFileField
from .mixins import BacklinkModelMixin, EditableResourceMixin

__all__ = [
    "CollectionItemBase",
    "CollectionFileItemBase",
    "CollectionBase",
    "FilePreviewMixin",
    "FileItemBase",
    "SVGItemBase",
    "ImageItemBase",
    "FileItem",
    "SVGItem",
    "ImageItem",
    "Collection",
    "ImageCollection",
]


class ItemTypesDescriptor:
    """
    Дескриптор, добавляемый к моделям коллекций.
    Возвращает упорядоченый словарь типов элементов коллекции,
    учитывая наследование.
    """

    def __init__(self, name):
        self.name = name

    def __get__(self, instance, cls=None) -> Dict[str, CollectionItem]:
        if cls is None:
            cls = type(instance)

        cache_attname = "_{}__item_type_cache".format(cls.__name__)
        if hasattr(cls, cache_attname):
            return OrderedDict(getattr(cls, cache_attname))

        item_types = OrderedDict()
        parents = [base for base in cls.__mro__ if issubclass(base, CollectionBase)]
        for base in reversed(parents):
            base_item_types = _get_item_types(base)
            if base_item_types is not None:
                undefined_item_types = set(item_types.keys()).difference(
                    base_item_types
                )
                item_types.update(base_item_types)

                # delete overridden item types
                for item_type_name in undefined_item_types:
                    if hasattr(base, item_type_name):
                        del item_types[item_type_name]

        # cache result in class object
        setattr(cls, cache_attname, tuple(item_types.items()))
        return item_types


class CollectionMeta(NoPermissionsMetaBase, ModelBase):
    """
    Хак, при котором вместо наследования создаются прокси-модели,
    если явно не указано обратное.
    """

    @classmethod
    def __prepare__(cls, name, bases):
        return OrderedDict()

    def __new__(mcs, name, bases, attrs, **kwargs):  # noqa: N804
        # set proxy=True by default
        meta = attrs.pop("Meta", None)
        if meta is None:
            meta = type("Meta", (), {"proxy": True})
        else:
            meta_attrs = meta.__dict__.copy()
            meta_attrs.setdefault("proxy", True)
            meta = type("Meta", meta.__bases__, meta_attrs)
        attrs["Meta"] = meta

        # сохраняем явно объявленные (не унаследованные) типы элементов коллекции
        # в приватное поле класса
        item_types = OrderedDict()
        for key, value in list(attrs.items()):
            if isinstance(value, CollectionItem):
                item_types[key] = value

        new_class = super().__new__(mcs, name, bases, attrs, **kwargs)
        _set_item_types(new_class, item_types)
        new_class.item_types = ItemTypesDescriptor("item_types")
        return new_class


class CollectionManager(models.Manager):
    """
    Из-за того, что в большинстве случаев коллекции являются прокси-моделями,
    любые запросы от имени такой модели будут работать с экземплярами конкретной
    модели (обычно Collection).

    Например, запрос
        MyProxyCollection.objects.all()
    вернёт все коллекции, а не только экземпляры MyCustomCollection.

    Данный менеджер ограничивает область действия подобных запросов.
    Для прокси-моделей запросы работают только с экземплярами данной прокси-модели.
    Для конкретных моделей поведение стандартное: запрос вернёт все экземпляры таблицы.
    """

    def get_queryset(self):
        if self.model._meta.proxy:
            collection_ct = ContentType.objects.get_for_model(
                self.model,
                for_concrete_model=False
            )
            return super().get_queryset().filter(
                collection_content_type=collection_ct
            )
        else:
            return super().get_queryset()


class CollectionBase(BacklinkModelMixin, metaclass=CollectionMeta):
    collection_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        editable=False,
        related_name="+"
    )
    concrete_collection_content_type = models.ForeignKey(
        ContentType,
        null=True,
        on_delete=models.CASCADE,
        editable=False,
        related_name="+"
    )
    items = ContentItemRelation(  # TODO: deprecated since v0.10.1
        "paper_uploads.CollectionItemBase",
        content_type_field="collection_content_type",
        object_id_field="collection_id",
        for_concrete_model=False,
    )
    created_at = models.DateTimeField(
        _("created at"),
        default=now,
        editable=False
    )
    modified_at = models.DateTimeField(
        _("changed at"),
        default=now,
        editable=False
    )

    default_mgr = models.Manager()  # fix migrations manager
    objects = CollectionManager()

    class Meta:
        proxy = False
        abstract = True
        default_permissions = ()
        default_manager_name = "default_mgr"
        verbose_name = _("collection")
        verbose_name_plural = _("collections")

    def __iter__(self):
        return self.get_items().iterator()

    def save(self, *args, **kwargs):
        if self.collection_content_type_id is None:
            self.collection_content_type = ContentType.objects.get_for_model(
                self, for_concrete_model=False
            )
        if self.concrete_collection_content_type_id is None:
            self.concrete_collection_content_type = ContentType.objects.get_for_model(
                self, for_concrete_model=True
            )
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        # Удаляем элементы группами, из-за рекурсии.
        # Удалить элементы с помощью `.all().delete()` - нельзя. Из-за того,
        # что в файле (django/db/models/deletion.py:284) указано следующее:
        #   model = new_objs[0].__class__
        # Это приводит к тому, что все полиморфные модели удаляются через модель
        # первого экземпляра в QuerySet.
        for item_type in self.item_types:
            self.get_items(item_type).delete()

        super().delete(using=using, keep_parents=keep_parents)

    @classmethod
    def _check_fields(cls, **kwargs):
        errors = super()._check_fields(**kwargs)
        for field in cls.item_types.values():
            errors.extend(field.check(**kwargs))
        return errors

    @classmethod
    def get_item_model(cls, item_type: str) -> 'Type[CollectionItemBase]':
        if item_type not in cls.item_types:
            raise exceptions.InvalidItemType(item_type)
        return cls.item_types[item_type].model

    def get_items(self, item_type: str = None) -> 'models.QuerySet[CollectionItemBase]':
        # Получение элементов коллекции работает как через прокси-модель,
        # так и через соответствующую конкретную модель.
        concrete_model_ct = ContentType.objects.get_for_model(self._meta.concrete_model)
        qs = CollectionItemBase.objects.filter(
            concrete_collection_content_type=concrete_model_ct,
            collection_id=self.pk
        ).order_by("order")

        if item_type is None:
            return qs

        if item_type not in self.item_types:
            raise exceptions.InvalidItemType(item_type)

        return qs.filter(type=item_type)

    def get_last_modified(self) -> datetime.datetime:
        """
        Получение даты модификации коллекции с учётом её элементов.
        """
        dates = [self.created_at, self.modified_at]
        item_date = self.get_items().aggregate(
            date=models.Max("modified_at")
        )["date"]

        if item_date is not None:
            dates.append(item_date)

        return max(*dates)


class Collection(CollectionBase):
    VARIATIONS: ClassVar[dict]

    class Meta:
        proxy = False  # явно указываем, что это не прокси-модель


# ======================================================================================


class CollectionItemMetaBase(PolymorphicModelBase, ResourceBaseMeta):
    pass


class CollectionItemBase(EditableResourceMixin, PolymorphicModel, Resource, metaclass=CollectionItemMetaBase):
    """
    Базовый класс элемента коллекции.
    """

    # путь к шаблону, представляющему элемент коллекции в админке
    template_name: Optional[str] = None

    # путь к шаблону, представляющему картинку-превью элемента коллекции в админке
    preview_template_name: Optional[str] = None

    collection_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="+"
    )
    concrete_collection_content_type = models.ForeignKey(
        ContentType,
        null=True,
        on_delete=models.CASCADE,
        editable=False,
        related_name="+"
    )
    collection_id = models.IntegerField()
    collection = GenericForeignKey(
        ct_field="collection_content_type",
        fk_field="collection_id",
        for_concrete_model=False,
    )

    type = models.CharField(
        _("type"),
        max_length=32,
        db_index=True,
        editable=False
    )
    order = models.IntegerField(
        _("order"),
        default=0,
        editable=False
    )

    class Meta:
        # Используется обратный порядок полей в составном индексе,
        # т.к. селективность поля collection_id выше, а для поля
        # `collection_content_type` уже есть отдельный индекс.
        index_together = [("collection_id", "collection_content_type")]
        verbose_name = _("item")
        verbose_name_plural = _("items")

    @classmethod
    def check(cls, **kwargs):
        return [
            *super().check(**kwargs),
            *cls._check_template_name(),
        ]

    @classmethod
    def _check_template_name(cls, **kwargs):
        if cls._meta.abstract or cls is CollectionItemBase:
            return []

        errors = []
        if cls.template_name is None:
            errors.append(
                checks.Error(
                    "{} requires a definition of 'template_name'".format(cls.__name__),
                    obj=cls,
                )
            )
        return errors

    @property
    def item_type(self):
        warnings.warn(
            "'item_type' is deprecated in favor of 'type'",
            DeprecationWarning,
            stacklevel=2
        )
        return self.type

    @item_type.setter
    def item_type(self, value: str):
        warnings.warn(
            "'item_type' is deprecated in favor of 'type'",
            DeprecationWarning,
            stacklevel=2
        )
        self.type = value

    def get_next_order_value(self):
        max_order = CollectionItemBase.objects.filter(
            collection_content_type_id=self.collection_content_type_id,
            collection_id=self.collection_id,
        ).aggregate(
            max_order=models.Max(Coalesce("order", 0))
        )["max_order"]

        return 0 if max_order is None else max_order + 1

    def save(self, *args, **kwargs):
        if self.concrete_collection_content_type_id is None and self.collection_content_type_id is not None:
            try:
                collection_cls = self.get_collection_class()
            except exceptions.CollectionModelNotFoundError:
                # TODO: Добавленный в такую коллекцию элемент не сможет быть
                #       получен через get_items().
                pass
            else:
                self.concrete_collection_content_type = ContentType.objects.get_for_model(
                    collection_cls,
                    for_concrete_model=True
                )

        if not self.pk and self.collection_id:
            # Попытка решить проблему того, что при создании коллекции элементы
            # отсортированы в порядке загрузки, а не в порядке добавления.
            # Код ниже не решает проблему полностью, но уменьшает её влияние.
            if self.order is None or self.collection.get_items().filter(order=self.order).exists():
                self.order = self.get_next_order_value()

        super().save(*args, **kwargs)

    @classmethod
    def accept(cls, *args, **kwargs) -> bool:
        """
        Возвращает True, если переданные данные могут быть представлены
        текущей моделью элемента коллекции.
        """
        raise NotImplementedError

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "collectionId": self.collection_id,
            "itemType": self.type,  # TODO: deprecated
            "type": self.type,
            "order": self.order,
            "preview": self.render_preview(),
        }

    def get_collection_class(self) -> Type[CollectionBase]:
        # Прямое обращение к полю `self.collection_content_type` дёргает БД.
        # Вместо него используется метод `get_for_id()` класса ContentType,
        # который использует общий кэш.
        # (!) Если класс модели для указанного ContentType удалён, то
        # метод вернёт None.
        collection_ct = ContentType.objects.get_for_id(self.collection_content_type_id)

        try:
            return apps.get_model(collection_ct.app_label, collection_ct.model)
        except LookupError:
            raise exceptions.CollectionModelNotFoundError(
                "{}.{}".format(collection_ct.app_label, collection_ct.model)
            )

    def get_item_type_field(self) -> CollectionItem:
        """
        Получение поля CollectionItem, с которым связан текущий элемент.
        """
        collection_cls = self.get_collection_class()

        field = collection_cls.item_types.get(self.type)
        if field is None:
            raise exceptions.CollectionItemNotFoundError()

        # support proxy models
        if self._meta.concrete_model is field.model._meta.concrete_model:
            return field

        raise exceptions.CollectionItemNotFoundError()

    def get_itemtype_field(self) -> Optional[CollectionItem]:
        warnings.warn(
            "'get_itemtype_field' is deprecated in favor of 'get_item_type_field'",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_item_type_field()

    def attach_to(self, collection: CollectionBase):
        """
        Подключение элемента к коллекции.
        """
        self.collection_content_type = ContentType.objects.get_for_model(
            collection, for_concrete_model=False
        )
        self.concrete_collection_content_type = ContentType.objects.get_for_model(
            collection, for_concrete_model=True
        )
        self.collection_id = collection.pk

        for name, field in collection.item_types.items():
            # support proxy models
            if self._meta.concrete_model is field.model._meta.concrete_model:
                self.type = name
                break
        else:
            raise exceptions.UnsupportedCollectionItemError(type(self).__name__)

    def render_preview(self):
        """ Отображение элемента коллекции в админке """
        context = self.get_preview_context()
        return loader.render_to_string(self.preview_template_name, context)

    def get_preview_context(self):
        return {
            "item": self,
            "width": settings.COLLECTION_ITEM_PREVIEW_WIDTH,
            "height": settings.COLLECTION_ITEM_PREVIEW_HEIGHT,
        }


class CollectionFileItemBase(CollectionItemBase, FileFieldResource):
    """
    Базовый класс элемента галереи, содержащего файл.
    """

    class Meta:
        abstract = True

    @classmethod
    def accept(cls, file: File) -> bool:
        raise NotImplementedError

    def get_file_storage(self) -> Storage:
        try:
            item_type_field = self.get_item_type_field()
        except (exceptions.CollectionModelNotFoundError, exceptions.CollectionItemNotFoundError):
            return default_storage

        storage = item_type_field.options.get("storage") or default_storage
        if callable(storage):
            storage = storage()
        return storage

    @classmethod
    def file_supported(cls, file: File) -> bool:
        warnings.warn(
            "file_supported() is deprecated in favor of accept()",
            DeprecationWarning,
            stacklevel=2
        )
        return cls.accept(file)


class FilePreviewMixin(models.Model):
    """
    Миксина элемента коллекции, добавляющая иконку для файла в админке
    """

    class Meta:
        abstract = True

    def get_preview_url(self):
        extension = self.extension.lower()  # noqa
        extension = FILE_ICON_OVERRIDES.get(extension, extension)
        icon_path_template = "paper_uploads/dist/assets/{}.svg"
        icon_path = icon_path_template.format(extension)
        if find(icon_path) is None:
            icon_path = icon_path_template.format(FILE_ICON_DEFAULT)
        return staticfiles_storage.url(icon_path)

    def get_preview_context(self):
        context = super().get_preview_context()  # noqa
        context.update(preview_url=self.get_preview_url())
        return context


# ======================================================================================


class FileItemBase(FilePreviewMixin, CollectionFileItemBase):
    change_form_class = "paper_uploads.forms.dialogs.collection.ChangeFileItemDialog"
    template_name = "paper_uploads/items/file.html"
    preview_template_name = "paper_uploads/items/preview/file.html"

    file = DynamicStorageFileField(
        _("file"),
        max_length=255,
    )
    display_name = models.CharField(
        _("display name"),
        max_length=255,
        blank=True
    )

    class Meta(CollectionItemBase.Meta):
        abstract = True
        verbose_name = _("File item")
        verbose_name_plural = _("File items")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.basename
        super().save(*args, **kwargs)

    def get_file_folder(self) -> str:
        try:
            item_type_field = self.get_item_type_field()
        except (exceptions.CollectionModelNotFoundError, exceptions.CollectionItemNotFoundError):
            return settings.COLLECTION_FILES_UPLOAD_TO

        return item_type_field.options.get("upload_to") or settings.COLLECTION_FILES_UPLOAD_TO

    def get_file(self) -> FieldFile:
        return self.file

    @classmethod
    def get_file_field(cls) -> models.FileField:
        return cls._meta.get_field("file")

    def get_caption(self):
        name = self.display_name or self.basename
        if self.extension:
            return "{}.{}".format(name, self.extension)
        return name

    @classmethod
    def accept(cls, file: File) -> bool:
        return True


class SVGItemBase(SVGFileResourceMixin, CollectionFileItemBase):
    change_form_class = "paper_uploads.forms.dialogs.collection.ChangeSVGItemDialog"
    template_name = "paper_uploads/items/svg.html"
    preview_template_name = "paper_uploads/items/preview/svg.html"

    file = DynamicStorageFileField(
        _("file"),
        max_length=255,
    )
    display_name = models.CharField(
        _("display name"),
        max_length=255,
        blank=True
    )

    class Meta(CollectionItemBase.Meta):
        abstract = True
        verbose_name = _("SVG item")
        verbose_name_plural = _("SVG items")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.basename
        super().save(*args, **kwargs)

    def get_file_folder(self) -> str:
        try:
            item_type_field = self.get_item_type_field()
        except (exceptions.CollectionModelNotFoundError, exceptions.CollectionItemNotFoundError):
            return settings.COLLECTION_FILES_UPLOAD_TO

        return item_type_field.options.get("upload_to") or settings.COLLECTION_FILES_UPLOAD_TO

    def get_file(self) -> FieldFile:
        return self.file

    @classmethod
    def get_file_field(cls) -> models.FileField:
        return cls._meta.get_field("file")

    def get_caption(self):
        name = self.display_name or self.basename
        if self.extension:
            return "{}.{}".format(name, self.extension)
        return name

    @classmethod
    def accept(cls, file: File) -> bool:
        filename, ext = posixpath.splitext(file.name)
        return ext.lower() == ".svg"


class ImageItemBase(VersatileImageResourceMixin, CollectionFileItemBase):
    PREVIEW_VARIATIONS = IMAGE_ITEM_VARIATIONS
    change_form_class = "paper_uploads.forms.dialogs.collection.ChangeImageItemDialog"
    template_name = "paper_uploads/items/image.html"
    preview_template_name = "paper_uploads/items/preview/image.html"

    file = VariationalFileField(
        _("file"),
        max_length=255,
    )

    class Meta(CollectionItemBase.Meta):
        abstract = True
        verbose_name = _("Image item")
        verbose_name_plural = _("Image items")

    def get_file_folder(self) -> str:
        try:
            item_type_field = self.get_item_type_field()
        except (exceptions.CollectionModelNotFoundError, exceptions.CollectionItemNotFoundError):
            return settings.COLLECTION_IMAGES_UPLOAD_TO

        return item_type_field.options.get("upload_to") or settings.COLLECTION_IMAGES_UPLOAD_TO

    def get_file(self) -> FieldFile:
        return self.file

    @classmethod
    def get_file_field(cls) -> VariationalFileField:
        return cls._meta.get_field("file")

    def recut_async(self, names: Iterable[str] = ()):
        """
        Превью для админки режутся сразу, а остальное — потом.
        """
        preview_variations = tuple(iterate_variation_names(self.PREVIEW_VARIATIONS))
        self.recut(names=preview_variations)

        if not names:
            names = self.get_variations().keys()

        rest_variations = tuple(set(names).difference(preview_variations))
        super().recut_async(rest_variations)

    @cached_method("_variations_cache")
    def get_variations(self) -> Dict[str, PaperVariation]:
        """
        Перебираем возможные места вероятного определения вариаций и берем
        первое непустое значение. Порядок проверки:
            1) параметр `variations` псевдо-поля `CollectionItem`
            2) член класса галереи VARIATIONS
        К найденному словарю примешиваются вариации для админки.
        """
        if not self.collection_content_type_id:
            raise cached_method.Bypass({})

        collection_cls = self.get_collection_class()
        item_type_field = self.get_item_type_field()
        variation_config = self.get_variation_config(collection_cls, item_type_field)
        return build_variations(variation_config)

    @classmethod
    def accept(cls, file: File) -> bool:
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # reset file position after mimetype detection
        basetype, subtype = mimetype.split("/", 1)
        return basetype == "image"

    @classmethod
    def get_variation_config(
        cls, collection_cls: Type[CollectionBase], item_type_field: CollectionItem,
    ) -> Dict[str, Any]:
        if "variations" in item_type_field.options:
            variations = item_type_field.options["variations"]
        else:
            variations = getattr(collection_cls, "VARIATIONS", None)

        variations = variations or {}
        variations = dict(cls.PREVIEW_VARIATIONS, **variations)
        return variations


class FileItem(FileItemBase):
    pass


class SVGItem(SVGItemBase):
    pass


class ImageItem(ImageItemBase):
    pass


# ==============================================================================


class ImageCollection(Collection):
    """
    Коллекция, позволяющая хранить только изображения.
    """
    image = CollectionItem(ImageItem)

    @classmethod
    def get_configuration(cls) -> Dict[str, Any]:
        return {
            "strictImageValidation": True,
            "acceptFiles": [
                "image/bmp",
                "image/gif",
                "image/jpeg",
                "image/png",
                # "image/svg+xml",
                "image/tiff",
                "image/webp",
            ],
        }
