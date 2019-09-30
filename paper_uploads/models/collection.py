import magic
import posixpath
from collections import OrderedDict
from typing import Dict, Type, Any, IO, Iterable
from django.db import models, DEFAULT_DB_ALIAS
from django.core import checks
from django.template import loader
from django.utils.timezone import now
from django.db.models import functions
from django.db.models.base import ModelBase
from django.utils.translation import gettext_lazy as _
from django.utils.module_loading import import_string
from django.contrib.staticfiles.finders import find
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from polymorphic.models import PolymorphicModel
from variations.variation import Variation
from .base import SlaveModelMixin, ProxyFileAttributesMixin
from .file import UploadedFileBase
from .image import UploadedImageBase, VariationalFileField
from .fields import CollectionItemTypeField
from ..conf import settings, FILE_ICON_OVERRIDES, FILE_ICON_DEFAULT
from ..storage import upload_storage
from .. import tasks
from .. import utils

__all__ = [
    'CollectionItemBase', 'FileItemBase', 'ImageItemBase', 'CollectionBase',
    'FileItem', 'ImageItem', 'SVGItem', 'Collection', 'ImageCollection'
]


class CollectionItemBase(PolymorphicModel):
    # Флаг для индикации базового класса элемента коллекции (см. метод checks).
    __BaseCollectionItem = True

    change_form_class = None
    admin_template_name = None

    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE)
    object_id = models.IntegerField()
    collection = GenericForeignKey(for_concrete_model=False)

    item_type = models.CharField(_('type'), max_length=32, db_index=True, editable=False)
    order = models.IntegerField(_('order'), default=0, editable=False)

    class Meta:
        default_permissions = ()

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
                    "{} requires a definition of 'change_form_class'".format(cls(__name__)),
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
                        "not exists" % (
                            cls.change_form_class
                        ),
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
                    "{} requires a definition of 'admin_template_name'".format(cls(__name__)),
                    obj=cls,
                )
            )
        return errors

    def save(self, *args, **kwargs):
        if not self.pk and not self.order:
            # добаление новых элементов в конец
            max_order = self.collection.items.aggregate(
                order=functions.Coalesce(models.Max('order'), 0)
            )['order']
            self.order = max_order + 1
        super().save(*args, **kwargs)

    def get_collection_class(self) -> Type['CollectionBase']:
        return self.content_type.model_class()

    def get_collection_field(self) -> CollectionItemTypeField:
        collection_cls = self.get_collection_class()
        for name, field in collection_cls.item_types.items():
            if field.model is type(self):
                return field

    def as_dict(self) -> Dict[str, Any]:
        """
        Словарь, возвращаемый в виде JSON после загрузки файла.
        Служит для формирования виджета файла без перезагрузки страницы.
        """
        return {
            'id': self.pk,
            'collectionId': self.object_id,
            'item_type': self.item_type,
        }

    @classmethod
    def check_file(cls, file: IO) -> bool:
        """
        Проверка загруженного файла на принадлежность текущему типу элемента галереи.
        Если укзанный файл поддерживается, метод должен вернуть True.
        """
        raise NotImplementedError

    def attach_to(self, collection: 'CollectionBase', commit: bool = True):
        """
        Подключение элемента к коллекции.
        Используется в случае динамического создания элементов колелкции.
        """
        self.content_type = ContentType.objects.get_for_model(collection, for_concrete_model=False)
        self.object_id = collection.pk
        for name, field in collection.item_types.items():
            if field.model is type(self):
                self.item_type = name
                break
        else:
            raise ValueError('Unsupported collection item: %s' % type(self).__name__)

        if commit:
            self.save()


class FileItemBase(ProxyFileAttributesMixin, CollectionItemBase, UploadedFileBase):
    admin_template_name = 'paper_uploads/collection_item/file.html'

    file = models.FileField(_('file'), max_length=255, storage=upload_storage,
        upload_to=settings.COLLECTION_FILES_UPLOAD_TO)
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(CollectionItemBase.Meta):
        abstract = True
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def __str__(self):
        return self.file.name

    def pre_save_new_file(self):
        super().pre_save_new_file()
        if not self.pk and not self.display_name:
            self.display_name = self.name

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.canonical_name,
            'url': self.file.url,
        }


class ImageItemBase(ProxyFileAttributesMixin, CollectionItemBase, UploadedImageBase):
    admin_template_name = 'paper_uploads/collection_item/image.html'
    PREVIEW_VARIATIONS = settings.COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS

    file = VariationalFileField(_('file'), max_length=255, storage=upload_storage,
        upload_to=settings.COLLECTION_IMAGES_UPLOAD_TO)

    class Meta(CollectionItemBase.Meta):
        abstract = True
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def __str__(self):
        return self.file.name

    def get_variations(self) -> Dict[str, Variation]:
        """
        Перебираем возможные места вероятного определения вариаций и берем
        первое непустое значение. Порядок проверки:
            1) параметр `variations` поля `CollectionItemTypeField`
            2) член класса галереи VARIATIONS
        К найденному словарю примешиваются вариации для админки.
        """
        if not hasattr(self, '_variations_cache'):
            item_type_field = self.get_collection_field()
            variations = item_type_field.extra.get('variations')
            if variations is None:
                collection_cls = self.get_collection_class()
                variations = getattr(collection_cls, 'VARIATIONS', None)

            variations = (variations or {}).copy()
            variations.update(self.PREVIEW_VARIATIONS)
            self._variations_cache = utils.build_variations(variations)
        return self._variations_cache

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.canonical_name,
            'url': self.file.url,
        }

    def post_save_new_file(self):
        """
        При отложенной нарезке превью для админки режутся сразу,
        а остальное - потом.
        """
        super(UploadedImageBase, self).post_save_new_file()
        if settings.RQ_ENABLED:
            preview_variations = tuple(self.PREVIEW_VARIATIONS.keys())
            self._recut_sync(names=preview_variations)
            self.recut(names=tuple(
                name
                for name in self.get_variations()
                if name not in preview_variations
            ))
        else:
            self.recut()


class CollectionMetaclass(ModelBase):
    """
    Хак, создающий прокси-модели вместо наследования, если явно не указано
    обратное.
    """
    def __new__(mcs, name, bases, attrs, **kwargs):
        new_attrs = {
            '_local_item_type_fields': []
        }
        for obj_name, obj in list(attrs.items()):
            new_attrs[obj_name] = obj

        # set proxy=True by default
        meta = new_attrs.pop('Meta', None)
        if meta is None:
            meta = type('Meta', (), {'proxy': True})
        elif not hasattr(meta, 'proxy'):
            meta = type('Meta', meta.__bases__, dict(meta.__dict__))
        new_attrs['Meta'] = meta

        new_class = super().__new__(mcs, name, bases, new_attrs, **kwargs)
        for base in bases:
            item_type_fields = getattr(base, '_local_item_type_fields', [])
            for field in item_type_fields:
                new_class.add_to_class(field.name, field)
        return new_class


class ItemTypesDescriptor:
    def __get__(self, instance, owner):
        if owner is None:
            owner = type(instance)
        return OrderedDict(
            (field.name, field)
            for field in owner._local_item_type_fields
        )


class ContentItemRelation(GenericRelation):
    """
    FIX: cascade delete polimorphic
    https://github.com/django-polymorphic/django-polymorphic/issues/34
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS):
        return super().bulk_related_objects(objs).non_polymorphic()


class CollectionBase(SlaveModelMixin, metaclass=CollectionMetaclass):
    item_types = ItemTypesDescriptor()
    items = ContentItemRelation(CollectionItemBase, for_concrete_model=False)
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
        for field in cls._local_item_type_fields:
            errors.extend(field.check(**kwargs))
        return errors

    def get_items(self, item_type: str = None):
        if item_type is None:
            return self.items.order_by('order')
        if item_type not in self.item_types:
            raise ValueError('Unsupported collection item type: %s' % item_type)
        return self.items.filter(item_type=item_type).order_by('order')

    def _recut_sync(self, names: Iterable[str] = (), using: str = DEFAULT_DB_ALIAS):
        recutable_items = tuple(
            name
            for name, field in self.item_types.items()
            if hasattr(field.model, 'recut')
        )
        for item in self.items.using(using).filter(item_type__in=recutable_items):
            item._recut_sync(names)

    def _recut_async(self, names: Iterable[str] = (), using: str = DEFAULT_DB_ALIAS):
        from django_rq.queues import get_queue
        queue = get_queue(settings.RQ_QUEUE_NAME)
        queue.enqueue_call(tasks.recut_collection, kwargs={
            'app_label': self._meta.app_label,
            'model_name': self._meta.model_name,
            'object_id': self.pk,
            'names': names,
            'using': using,
        })

    def recut(self, names: Iterable[str] = None, using: str = DEFAULT_DB_ALIAS):
        if settings.RQ_ENABLED:
            self._recut_async(names, using=using)
        else:
            self._recut_sync(names, using=using)


# ==============================================================================


class FileItem(FileItemBase):
    change_form_class = 'paper_uploads.forms.dialogs.collection.FileItemDialog'

    preview = models.CharField(_('preview URL'), max_length=255, blank=True, editable=False)

    @classmethod
    def check_file(cls, file: IO) -> bool:
        return True

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'preview': loader.render_to_string('paper_uploads/collection_item/preview/file.html', {
                'item': self,
                'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            })
        }

    def pre_save_new_file(self):
        super().pre_save_new_file()
        self.preview = self.get_preview_url()

    def get_preview_url(self):
        icon_path_template = 'paper_uploads/dist/image/{}.svg'
        extension = FILE_ICON_OVERRIDES.get(self.extension, self.extension)
        icon_path = icon_path_template.format(extension)
        if find(icon_path) is None:
            icon_path = icon_path_template.format(FILE_ICON_DEFAULT)
        return staticfiles_storage.url(icon_path)


class SVGItem(FileItemBase):
    change_form_class = 'paper_uploads.forms.dialogs.collection.FileItemDialog'
    admin_template_name = 'paper_uploads/collection_item/svg.html'

    class Meta(CollectionItemBase.Meta):
        verbose_name = _('SVG-file')
        verbose_name_plural = _('SVG-files')

    @classmethod
    def check_file(cls, file: IO) -> bool:
        filename, ext = posixpath.splitext(file.name)
        return ext.lower() == '.svg'

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'preview': loader.render_to_string('paper_uploads/collection_item/preview/svg.html', {
                'item': self,
                'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            })
        }

    def post_save_new_file(self):
        super().post_save_new_file()

        # postprocess svg
        collection_field = self.get_collection_field()
        if collection_field is not None:
            postprocess_options = collection_field.extra.get('postprocess')
        else:
            postprocess_options = None
        # TODO: явный запрет постобработки
        utils.postprocess_svg(self.file.name, postprocess_options)


class ImageItem(ImageItemBase):
    change_form_class = 'paper_uploads.forms.dialogs.collection.ImageItemDialog'

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.canonical_name,
            'url': self.file.url,
            'preview': loader.render_to_string('paper_uploads/collection_item/preview/image.html', {
                'item': self,
                'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            })
        }

    @classmethod
    def check_file(cls, file: IO) -> bool:
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)    # correct file position after mimetype detection
        basetype, subtype = mimetype.split('/', 1)
        return basetype == 'image'


class CollectionManager(models.Manager):
    """
    Из-за того, что все галереи являются прокси-моделями, запросы от имени
    любого из классов галереи затрагивает абсолютно все объекты галереи.
    С помощью этого менеджера можно работать только с галерями текущего типа.
    """
    def get_queryset(self):
        collection_ct = ContentType.objects.get_for_model(self.model, for_concrete_model=False)
        return super().get_queryset().filter(collection_content_type=collection_ct)


class Collection(CollectionBase):
    # поле, ссылающееся на одно из изображений коллекции (для экономии SQL-запросов)
    cover = models.ForeignKey(ImageItem, verbose_name=_('cover image'),
        null=True, editable=False, on_delete=models.SET_NULL)
    collection_content_type = models.ForeignKey(ContentType, null=True, on_delete=models.SET_NULL, editable=False)

    default_mgr = models.Manager()     # fix migrations manager
    objects = CollectionManager()

    class Meta:
        proxy = False   # явно указываем, что это не проски-модель
        default_manager_name = 'default_mgr'

    def save(self, *args, **kwargs):
        if not self.collection_content_type:
            self.collection_content_type = ContentType.objects.get_for_model(self,
                for_concrete_model=False
            )
        super().save(*args, **kwargs)


class ImageCollection(Collection):
    """
    Галерея, позволяющая хранить только изображения.
    """
    image = CollectionItemTypeField(ImageItem)

    @classmethod
    def get_validation(cls) -> Dict[str, Any]:
        return {
            **super().get_validation(),
            'acceptFiles': 'image/*',
        }
