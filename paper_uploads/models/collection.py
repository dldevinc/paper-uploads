import posixpath
from collections import OrderedDict
from typing import Any, Dict, Iterable, Optional, Type

import magic
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.finders import find
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core import checks
from django.core.files import File
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.fields.files import FieldFile
from django.db.models.functions import Coalesce
from django.template import loader
from django.utils.module_loading import import_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from polymorphic.base import PolymorphicModelBase
from polymorphic.models import PolymorphicModel

from ..conf import FILE_ICON_DEFAULT, FILE_ICON_OVERRIDES, settings
from ..helpers import _get_item_types, _set_item_types, build_variations
from ..storage import upload_storage
from ..variations import PaperVariation
from .base import (
    FileFieldResource,
    NoPermissionsMetaBase,
    ResourceBaseMeta,
    VersatileImageResourceMixin,
)
from .fields import CollectionItem
from .fields.collection import ContentItemRelation
from .image import VariationalFileField
from .mixins import BacklinkModelMixin
from .utils import generate_filename

__all__ = [
    "CollectionItemBase",
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

    def __get__(self, instance, cls=None):
        if cls is None:
            cls = type(instance)

        cache_attname = "_{}__item_type_cache".format(cls.__name__)
        if hasattr(cls, cache_attname):
            return OrderedDict(getattr(cls, cache_attname))

        item_types = OrderedDict()
        parents = [base for base in cls.mro() if issubclass(base, CollectionBase)]
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


class CollectionBase(BacklinkModelMixin, metaclass=CollectionMeta):
    items = ContentItemRelation(
        "paper_uploads.CollectionItemBase",
        content_type_field="collection_content_type",
        object_id_field="collection_id",
        for_concrete_model=False,
    )
    created_at = models.DateTimeField(_("created at"), default=now, editable=False)

    class Meta:
        proxy = False
        abstract = True
        default_permissions = ()
        verbose_name = _("collection")
        verbose_name_plural = _("collections")

    def delete(self, using=None, keep_parents=False):
        # Удаляем элементы вручную из-за рекурсии (см. clean_uploads.py, строка 145)
        # Удалить элементы с помощью `.all().delete()` нельзя из-за того, что в
        # файле (django/db/models/deletion.py:248) указано следующее:
        #   model = new_objs[0].__class__
        # Это приводит к тому, что все полиморфные модели удаляются через модель
        # первой модели в спсике.
        for item_type in self.item_types:
            self.get_items(item_type).delete()

        super().delete(using=using, keep_parents=keep_parents)

    @classmethod
    def _check_fields(cls, **kwargs):
        errors = super()._check_fields(**kwargs)
        for field in cls.item_types.values():
            errors.extend(field.check(**kwargs))
        return errors

    def get_items(self, item_type: str = None) -> 'models.QuerySet[CollectionItemBase]':
        # TODO: что если класс элемента был удален из коллекции, но элементы остались?
        if item_type is None:
            return self.items.order_by("order")
        if item_type not in self.item_types:
            raise ValueError(_("Unsupported collection item type: %s") % item_type)
        return self.items.filter(item_type=item_type).order_by("order")

    def detect_item_type(self, *args, **kwargs) -> Optional[str]:
        """
        Генератор, поочередно проверяющий классы элементов коллекции
        на возможность представления данных, переданных в параметрах.
        """
        for item_type, field in self.item_types.items():
            if hasattr(field.model, "file_supported"):
                if field.model.file_supported(*args, **kwargs):
                    yield item_type


class CollectionManager(models.Manager):
    """
    Из-за того, что все галереи являются прокси-моделями, запросы от имени
    любого из классов галереи затрагивает абсолютно все объекты галереи.
    С помощью этого менеджера можно работать только с галереями текущего типа.
    """

    def get_queryset(self):
        collection_ct = ContentType.objects.get_for_model(
            self.model, for_concrete_model=False
        )
        return super().get_queryset().filter(collection_content_type=collection_ct)


class Collection(CollectionBase):
    collection_content_type = models.ForeignKey(
        ContentType, null=True, on_delete=models.SET_NULL, editable=False
    )

    default_mgr = models.Manager()  # fix migrations manager
    objects = CollectionManager()

    class Meta:
        proxy = False  # явно указываем, что это не прокси-модель
        default_manager_name = "default_mgr"

    def save(self, *args, **kwargs):
        if not self.collection_content_type:
            self.collection_content_type = ContentType.objects.get_for_model(
                self, for_concrete_model=False
            )
        super().save(*args, **kwargs)


# ======================================================================================


class CollectionItemMetaBase(PolymorphicModelBase, ResourceBaseMeta):
    pass


class CollectionItemBase(PolymorphicModel, metaclass=CollectionItemMetaBase):
    """
    Базовый класс элемента коллекции.
    """

    # Флаг для индикации базового класса элемента коллекции.
    # См. метод _check_form_class()
    __BaseCollectionItem = True

    change_form_class: Optional[str] = None

    # путь к шаблону, представляющему элемент коллекции в админке
    template_name: Optional[str] = None

    # путь к шаблону, представляющему картинку-превью элемента коллекции в админке
    preview_template_name: Optional[str] = None

    collection_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    collection_id = models.IntegerField()
    collection = GenericForeignKey(
        ct_field="collection_content_type",
        fk_field="collection_id",
        for_concrete_model=False,
    )

    item_type = models.CharField(
        _("type"), max_length=32, db_index=True, editable=False
    )
    order = models.IntegerField(_("order"), default=0, editable=False)

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    @classmethod
    def check(cls, **kwargs):
        return [
            *super().check(**kwargs),
            *cls._check_form_class(),
            *cls._check_template_name(),
        ]

    @classmethod
    def _check_form_class(cls, **kwargs):
        flag = "_{}__BaseCollectionItem".format(cls.__name__)
        if getattr(cls, flag, None) is True or cls._meta.abstract:
            return []

        errors = []
        if cls.change_form_class is None:
            errors.append(
                checks.Error(
                    "{} requires a definition of 'change_form_class'".format(
                        cls.__name__
                    ),
                    obj=cls,
                )
            )
        else:
            try:
                import_string(cls.change_form_class)
            except ImportError:
                errors.append(
                    checks.Error(
                        "The value of 'change_form_class' refers to '%s', which does "
                        "not exists" % cls.change_form_class,
                        obj=cls,
                    )
                )
        return errors

    @classmethod
    def _check_template_name(cls, **kwargs):
        flag = "_{}__BaseCollectionItem".format(cls.__name__)
        if getattr(cls, flag, None) is True or cls._meta.abstract:
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

    def get_order(self):
        max_order = CollectionItemBase.objects.filter(
            collection_content_type_id=self.collection_content_type_id,
            collection_id=self.collection_id,
        ).aggregate(
            max_order=models.Max(Coalesce("order", 0))
        )["max_order"]

        return 0 if max_order is None else max_order + 1

    def save(self, *args, **kwargs):
        if not self.pk:
            # Попытка решить проблему того, что при создании коллекции,
            # элементы отсортированы в порядке загрузки, а не в порядке
            # добавления. Код ниже не решает проблему полностью,
            # но уменьшает её влияние.
            if self.order is None or self.collection.items.filter(order=self.order).exists():
                self.order = self.get_order()
        super().save(*args, **kwargs)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "collectionId": self.collection_id,
            "itemType": self.item_type,
            "caption": self.get_caption(),
            "order": self.order,
            "preview": self.render_preview(),
        }

    def get_collection_class(self) -> Type[CollectionBase]:
        return self.collection_content_type.model_class()

    def get_itemtype_field(self) -> Optional[CollectionItem]:
        collection_cls = self.get_collection_class()
        for name, field in collection_cls.item_types.items():
            if field.model is type(self):
                return field
        return None

    def attach_to(self, collection: CollectionBase):
        """
        Подключение элемента к коллекции.
        """
        self.collection_content_type = ContentType.objects.get_for_model(
            collection, for_concrete_model=False
        )
        self.collection_id = collection.pk
        for name, field in collection.item_types.items():
            if field.model is type(self):
                self.item_type = name
                break
        else:
            raise TypeError(_("Unsupported collection item: %s") % type(self).__name__)

    def get_caption(self):
        """ Заголовок для виджета в админке """
        return self.get_basename()

    def render_preview(self):
        """ Отображение элемента коллекции в админке """
        context = self.get_preview_context()
        return loader.render_to_string(self.preview_template_name, context)

    def get_preview_context(self):
        return {
            "item": self,
            "width": settings.COLLECTION_ITEM_PREVIEW_WIDTH,
            "height": settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
        }


class CollectionFileItemBase(CollectionItemBase, FileFieldResource, metaclass=CollectionItemMetaBase):
    """
    Базовый класс элемента галереи, содержащего файл.
    """

    class Meta:
        abstract = True

    @classmethod
    def file_supported(cls, file: File) -> bool:
        """
        Проверка возможности представления загруженного файла
        текущим классом элемента в коллекции.
        """
        raise NotImplementedError


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
    change_form_class = "paper_uploads.forms.dialogs.collection.FileItemDialog"
    template_name = "paper_uploads/items/file.html"
    preview_template_name = "paper_uploads/items/preview/file.html"

    file = models.FileField(
        _("file"),
        max_length=255,
        storage=upload_storage,
        upload_to=generate_filename,
    )
    display_name = models.CharField(_("display name"), max_length=255, blank=True)

    class Meta(CollectionItemBase.Meta):
        abstract = True
        verbose_name = _("File item")
        verbose_name_plural = _("File items")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.basename
        super().save(*args, **kwargs)

    def get_file_folder(self) -> str:
        return settings.COLLECTION_FILES_UPLOAD_TO

    def get_file(self) -> FieldFile:
        return self.file

    def set_file(self, value):
        self.file = value

    def get_file_field(self) -> models.FileField:
        return self._meta.get_field("file")

    @classmethod
    def file_supported(cls, file: File) -> bool:
        return True


class SVGItemBase(CollectionFileItemBase):
    change_form_class = "paper_uploads.forms.dialogs.collection.FileItemDialog"
    template_name = "paper_uploads/items/svg.html"
    preview_template_name = "paper_uploads/items/preview/svg.html"

    file = models.FileField(
        _("file"),
        max_length=255,
        storage=upload_storage,
        upload_to=generate_filename,
    )
    display_name = models.CharField(_("display name"), max_length=255, blank=True)

    class Meta(CollectionItemBase.Meta):
        abstract = True
        verbose_name = _("SVG item")
        verbose_name_plural = _("SVG items")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.basename
        super().save(*args, **kwargs)

    def get_file_folder(self) -> str:
        return settings.COLLECTION_FILES_UPLOAD_TO

    def get_file(self) -> FieldFile:
        return self.file

    def set_file(self, value):
        self.file = value

    def get_file_field(self) -> models.FileField:
        return self._meta.get_field("file")

    @classmethod
    def file_supported(cls, file: File) -> bool:
        filename, ext = posixpath.splitext(file.name)
        return ext.lower() == ".svg"


class ImageItemBase(VersatileImageResourceMixin, CollectionFileItemBase):
    PREVIEW_VARIATIONS = settings.COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS
    change_form_class = "paper_uploads.forms.dialogs.collection.ImageItemDialog"
    template_name = "paper_uploads/items/image.html"
    preview_template_name = "paper_uploads/items/preview/image.html"

    file = VariationalFileField(
        _("file"),
        max_length=255,
        storage=upload_storage,
        upload_to=generate_filename,
    )

    class Meta(CollectionItemBase.Meta):
        abstract = True
        verbose_name = _("Image item")
        verbose_name_plural = _("Image items")

    def get_file_folder(self) -> str:
        return settings.COLLECTION_IMAGES_UPLOAD_TO

    def get_file(self) -> FieldFile:
        return self.file

    def set_file(self, value):
        self.file = value

    def get_file_field(self) -> VariationalFileField:
        return self._meta.get_field("file")

    def recut_async(self, names: Iterable[str] = ()):
        """
        Превью для админки режутся сразу, а остальное — потом.
        """
        preview_variations = tuple(self.PREVIEW_VARIATIONS.keys())
        self.recut(names=preview_variations)

        other_variations = tuple(set(names).difference(preview_variations))
        super().recut_async(other_variations)

    def get_variations(self) -> Dict[str, PaperVariation]:
        """
        Перебираем возможные места вероятного определения вариаций и берем
        первое непустое значение. Порядок проверки:
            1) параметр `variations` псевдо-поля `CollectionItem`
            2) член класса галереи VARIATIONS
        К найденному словарю примешиваются вариации для админки.
        """
        if not hasattr(self, "_variations_cache"):
            collection_cls = self.get_collection_class()
            itemtype_field = self.get_itemtype_field()
            variation_config = self.get_variation_config(itemtype_field, collection_cls)
            self._variations_cache = build_variations(variation_config)
        return self._variations_cache

    @classmethod
    def file_supported(cls, file: File) -> bool:
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # correct file position after mimetype detection
        basetype, subtype = mimetype.split("/", 1)
        return basetype == "image"

    @classmethod
    def get_variation_config(
        cls, rel: Optional[CollectionItem], collection_cls: Type[CollectionBase]
    ) -> Dict[str, Any]:
        if rel is not None and "variations" in rel.options:
            variations = rel.options["variations"]
        else:
            variations = getattr(collection_cls, "VARIATIONS", None)
        variations = (variations or {}).copy()
        variations.update(cls.PREVIEW_VARIATIONS)
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
