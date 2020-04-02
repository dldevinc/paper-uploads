import posixpath
from collections import OrderedDict
from typing import Any, Dict, Optional, Type

import magic
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.finders import find
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core import checks
from django.core.files import File
from django.db import DEFAULT_DB_ALIAS, models
from django.db.models import functions
from django.db.models.base import ModelBase
from django.db.models.fields.files import FieldFile
from django.template import loader
from django.utils.module_loading import import_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel

from ..conf import FILE_ICON_DEFAULT, FILE_ICON_OVERRIDES, settings
from ..helpers import build_variations
from ..postprocess import postprocess_common_file, postprocess_variation
from ..storage import upload_storage
from ..variations import PaperVariation
from .base import (
    PostprocessableFileFieldResource,
    ReadonlyFileProxyMixin,
    Resource,
    ReverseFieldModelMixin,
    VariationFile,
    VersatileImageResourceMixin,
)
from .fields import FormattedFileField, ItemField
from .image import VariationalFileField

__all__ = [
    'CollectionResourceItem',
    'CollectionBase',
    'FileItem',
    'SVGItem',
    'ImageItem',
    'Collection',
    'ImageCollection',
]


class CollectionResourceItem(PolymorphicModel):
    # Флаг для индикации базового класса элемента коллекции.
    # См. метод _check_form_class()
    __BaseCollectionItem = True

    change_form_class = None
    admin_template_name = None

    collection_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    collection_id = models.IntegerField()
    collection = GenericForeignKey(
        ct_field='collection_content_type',
        fk_field='collection_id',
        for_concrete_model=False,
    )

    item_type = models.CharField(
        _('type'), max_length=32, db_index=True, editable=False
    )
    order = models.IntegerField(_('order'), default=0, editable=False)

    class Meta(Resource.Meta):
        default_permissions = ()
        verbose_name = _('item')
        verbose_name_plural = _('items')

    @classmethod
    def check(cls, **kwargs):
        return [
            *super().check(**kwargs),
            *cls._check_form_class(),
            *cls._check_template_name(),
        ]

    @classmethod
    def _check_form_class(cls, **kwargs):
        flag = '_{}__BaseCollectionItem'.format(cls.__name__)
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
                        "not exists" % (cls.change_form_class),
                        obj=cls,
                    )
                )
        return errors

    @classmethod
    def _check_template_name(cls, **kwargs):
        flag = '_{}__BaseCollectionItem'.format(cls.__name__)
        if getattr(cls, flag, None) is True or cls._meta.abstract:
            return []

        errors = []
        if cls.admin_template_name is None:
            errors.append(
                checks.Error(
                    "{} requires a definition of 'admin_template_name'".format(
                        cls.__name__
                    ),
                    obj=cls,
                )
            )
        return errors

    def save(self, *args, **kwargs):
        if not self.pk:
            # попытка решить проблему того, что при создании коллекции,
            # элементы отсортированы в порядке загрузки, а не в порядке
            # добавления. Код ниже не решает проблему, но уменьшает её влияние.
            if self.collection.items.filter(order=self.order).exists():
                max_order = self.collection.items.aggregate(
                    order=functions.Coalesce(models.Max('order'), 0)
                )['order']
                self.order = max_order + 1
        super().save(*args, **kwargs)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'collectionId': self.collection_id,
            'item_type': self.item_type,
            'caption': self.caption,
            'preview': self.preview,
        }

    def get_collection_class(self) -> Type['CollectionBase']:
        return self.collection_content_type.model_class()

    def get_itemtype_field(self) -> ItemField:
        collection_cls = self.get_collection_class()
        for name, field in collection_cls.item_types.items():
            if field.model is type(self):
                return field

    def attach_to(self, collection: 'CollectionBase'):
        """
        Подключение элемента к коллекции.
        Используется в случае динамического создания элементов коллекции.
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
            raise ValueError('Unsupported collection item: %s' % type(self).__name__)

    @property
    def caption(self):
        """ Заголовок для виджета в админке """
        raise NotImplementedError

    @property
    def preview(self):
        """ Картинка-превью для виджета в админке """
        raise NotImplementedError


class FilePreviewItemMixin(models.Model):
    preview_url = models.CharField(
        _('preview URL'), max_length=255, blank=True, editable=False
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.preview_url = self.get_preview_url()
        super().save(*args, **kwargs)

    @property
    def preview(self):
        return loader.render_to_string(
            'paper_uploads/collection_item/preview/file.html',
            {
                'item': self,
                'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            },
        )

    def get_preview_url(self):
        icon_path_template = 'paper_uploads/dist/image/{}.svg'
        extension = FILE_ICON_OVERRIDES.get(self.extension, self.extension)
        icon_path = icon_path_template.format(extension)
        if find(icon_path) is None:
            icon_path = icon_path_template.format(FILE_ICON_DEFAULT)
        return staticfiles_storage.url(icon_path)


class FileItem(
    FilePreviewItemMixin,
    ReadonlyFileProxyMixin,
    CollectionResourceItem,
    PostprocessableFileFieldResource,
):
    change_form_class = 'paper_uploads.forms.dialogs.collection.FileItemDialog'
    admin_template_name = 'paper_uploads/collection_item/file.html'

    file = FormattedFileField(
        _('file'),
        max_length=255,
        storage=upload_storage,
        upload_to=settings.COLLECTION_FILES_UPLOAD_TO,
    )
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(CollectionResourceItem.Meta):
        verbose_name = _('File item')
        verbose_name_plural = _('File items')

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def get_file(self) -> FieldFile:
        return self.file

    def postprocess(self, **kwargs):
        itemtype_field = self.get_itemtype_field()
        if itemtype_field is None:
            return

        postprocess_common_file(self.get_file(), field=itemtype_field)

        # обновление данных после обработки файла
        with self.get_file().open() as file:
            if self.update_hash(file):
                self.size = file.size
                self.modified_at = now()
                self.save(update_fields=['hash', 'size', 'modified_at'])

    @property
    def caption(self):
        return self.get_basename()

    @classmethod
    def file_supported(cls, file: File) -> bool:
        # TODO: магический метод
        return True


class SVGItem(
    ReadonlyFileProxyMixin, CollectionResourceItem, PostprocessableFileFieldResource
):
    change_form_class = 'paper_uploads.forms.dialogs.collection.FileItemDialog'
    admin_template_name = 'paper_uploads/collection_item/svg.html'

    file = FormattedFileField(
        _('file'),
        max_length=255,
        storage=upload_storage,
        upload_to=settings.COLLECTION_FILES_UPLOAD_TO,
    )
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(CollectionResourceItem.Meta):
        verbose_name = _('SVG item')
        verbose_name_plural = _('SVG items')

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def get_file(self) -> FieldFile:
        return self.file

    def postprocess(self, **kwargs):
        itemtype_field = self.get_itemtype_field()
        if itemtype_field is None:
            return

        postprocess_common_file(self.get_file(), field=itemtype_field)

        # обновление данных после обработки файла
        with self.get_file().open() as file:
            if self.update_hash(file):
                self.size = file.size
                self.modified_at = now()
                self.save(update_fields=['hash', 'size', 'modified_at'])

    @property
    def caption(self):
        return self.get_basename()

    @property
    def preview(self):
        return loader.render_to_string(
            'paper_uploads/collection_item/preview/svg.html',
            {
                'item': self,
                'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            },
        )

    @classmethod
    def file_supported(cls, file: File) -> bool:
        # TODO: магический метод
        filename, ext = posixpath.splitext(file.name)
        return ext.lower() == '.svg'


class ImageItem(
    ReadonlyFileProxyMixin,
    VersatileImageResourceMixin,
    CollectionResourceItem,
    PostprocessableFileFieldResource,
):
    PREVIEW_VARIATIONS = settings.COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS
    change_form_class = 'paper_uploads.forms.dialogs.collection.ImageItemDialog'
    admin_template_name = 'paper_uploads/collection_item/image.html'

    file = VariationalFileField(
        _('file'),
        max_length=255,
        storage=upload_storage,
        upload_to=settings.COLLECTION_IMAGES_UPLOAD_TO,
    )

    class Meta(CollectionResourceItem.Meta):
        verbose_name = _('Image item')
        verbose_name_plural = _('Image items')

    def get_file(self) -> FieldFile:
        return self.file

    def postprocess(self, **kwargs):
        # Исходник изображения не обрабатываем
        pass

    def postprocess_variation(self, file: VariationFile, variation: PaperVariation):
        itemtype_field = self.get_itemtype_field()
        postprocess_variation(file, variation, field=itemtype_field)

    def recut_async(self, **kwargs):
        """
        Превью для админки режутся сразу, а остальное — потом.
        """
        preview_variations = tuple(self.PREVIEW_VARIATIONS.keys())
        self._recut_sync(names=preview_variations)

        names = tuple(
            name
            for name in kwargs.get('names', None) or self.get_variations().keys()
            if name not in preview_variations
        )
        kwargs['names'] = names
        super().recut_async(**kwargs)

    def get_variations(self) -> Dict[str, PaperVariation]:
        """
        Перебираем возможные места вероятного определения вариаций и берем
        первое непустое значение. Порядок проверки:
            1) параметр `variations` поля `ItemField`
            2) член класса галереи VARIATIONS
        К найденному словарю примешиваются вариации для админки.
        """
        if not hasattr(self, '_variations_cache'):
            collection_cls = self.get_collection_class()
            itemtype_field = self.get_itemtype_field()
            variation_configs = self._get_variation_configs(
                itemtype_field, collection_cls
            )
            self._variations_cache = build_variations(variation_configs)
        return self._variations_cache

    @property
    def caption(self):
        return self.get_basename()

    @property
    def preview(self):
        return loader.render_to_string(
            'paper_uploads/collection_item/preview/image.html',
            {
                'item': self,
                'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            },
        )

    @classmethod
    def file_supported(cls, file: File) -> bool:
        # TODO: магический метод
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # correct file position after mimetype detection
        basetype, subtype = mimetype.split('/', 1)
        return basetype == 'image'

    @classmethod
    def _get_variation_configs(cls, field, collection_cls) -> Dict[str, Any]:
        if 'variations' in field.options:
            variations = field.options['variations']
        else:
            variations = getattr(collection_cls, 'VARIATIONS', None)
        variations = (variations or {}).copy()
        variations.update(cls.PREVIEW_VARIATIONS)
        return variations


# ==============================================================================


class ContentItemRelation(GenericRelation):
    """
    FIX: cascade delete polymorphic
    https://github.com/django-polymorphic/django-polymorphic/issues/34
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS):
        return super().bulk_related_objects(objs).non_polymorphic()


class CollectionMetaclass(ModelBase):
    """
    Хак, создающий прокси-модели вместо наследования, если явно не указано обратное.
    """

    @classmethod
    def __prepare__(self, name, bases):
        return OrderedDict()

    def __new__(mcs, name, bases, attrs, **kwargs):
        # set proxy=True by default
        meta = attrs.pop('Meta', None)
        if meta is None:
            meta = type('Meta', (), {'proxy': True})
        else:
            meta_attrs = meta.__dict__.copy()
            meta_attrs.setdefault('proxy', True)
            meta = type('Meta', meta.__bases__, meta_attrs)
        attrs['Meta'] = meta

        item_types_attribute = '_{}__item_types'.format(name)
        attrs[item_types_attribute] = original_item_types = OrderedDict()
        new_class = super().__new__(mcs, name, bases, attrs, **kwargs)

        # дескриптор, дающий доступ к item_types в режиме только для чтения
        new_class.item_types = ItemTypesDescriptor('item_types')

        # Django использует словарь для contributable_attrs, что приводит
        # к нарушению порядка подключения типов данных. Сортируем их сами.
        item_types = OrderedDict()
        for key in attrs:
            if key in original_item_types:
                item_types[key] = original_item_types[key]
        original_item_types.clear()
        original_item_types.update(item_types)

        return new_class


class ItemTypesDescriptor:
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, cls=None):
        if cls is None:
            cls = type(instance)

        item_types = OrderedDict()
        for base in reversed(cls.mro()):
            base_item_types = self.get_item_types(base)
            if base_item_types is not None:
                item_types.update(base_item_types)

        if instance is not None:
            instance.__dict__[self.name] = item_types
        return item_types

    def get_item_types(self, cls):
        item_types_attribute = '_{}__item_types'.format(cls.__name__)
        return getattr(cls, item_types_attribute, None)


class CollectionBase(ReverseFieldModelMixin, metaclass=CollectionMetaclass):
    items = ContentItemRelation(
        'paper_uploads.CollectionResourceItem',
        content_type_field='collection_content_type',
        object_id_field='collection_id',
        for_concrete_model=False,
    )
    created_at = models.DateTimeField(_('created at'), default=now, editable=False)

    class Meta:
        proxy = False
        abstract = True
        default_permissions = ()
        verbose_name = _('collection')
        verbose_name_plural = _('collectionы')

    @classmethod
    def _check_fields(cls, **kwargs):
        errors = super()._check_fields(**kwargs)
        for field in cls.item_types.values():
            errors.extend(field.check(**kwargs))
        return errors

    def get_items(self, item_type: str = None):
        if item_type is None:
            return self.items.order_by('order')
        if item_type not in self.item_types:
            raise ValueError('Unsupported collection item type: %s' % item_type)
        return self.items.filter(item_type=item_type).order_by('order')

    def detect_file_type(self, file: File) -> Optional[str]:
        raise NotImplementedError


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
        default_manager_name = 'default_mgr'

    def save(self, *args, **kwargs):
        if not self.collection_content_type:
            self.collection_content_type = ContentType.objects.get_for_model(
                self, for_concrete_model=False
            )
        super().save(*args, **kwargs)

    def detect_file_type(self, file: File) -> Optional[str]:
        """
        Определение класса элемента, которому нужно отнести загружаемый файл.
        """
        for item_type, field in self.item_types.items():
            file_supported = getattr(field.model, 'file_supported', None)
            if file_supported is not None and callable(file_supported):
                if file_supported(file):
                    return item_type


class ImageCollection(Collection):
    """
    Коллекция, позволяющая хранить только изображения.
    """

    image = ItemField(ImageItem)

    @classmethod
    def get_validation(cls) -> Dict[str, Any]:
        # TODO: магический метод
        return {
            'acceptFiles': ['image/*'],
        }

    def detect_file_type(self, file: File) -> Optional[str]:
        return 'image'
