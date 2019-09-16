import magic
import posixpath
from collections import OrderedDict
from django.db import models, DEFAULT_DB_ALIAS
from django.core import checks
from django.template import loader
from django.utils.timezone import now
from django.db.models import functions
from django.db.models.base import ModelBase
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.utils.module_loading import import_string
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from polymorphic.models import PolymorphicModel
from .base import SlaveModelMixin
from .file import UploadedFileBase
from .image import UploadedImageBase
from .fields import GalleryItemTypeField
from ..conf import settings, FILE_ICONS, FILE_ICON_DEFAULT
from ..storage import upload_storage
from .. import tasks
from .. import utils


class GalleryItemBase(PolymorphicModel):
    # Флаг для индикации базового класса элемента галереи (см. метод checks).
    __BaseGalleryItem = True

    FORM_CLASS = None
    TEMPLATE_NAME = None

    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE)
    object_id = models.IntegerField()
    gallery = GenericForeignKey(for_concrete_model=False)

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
        flag = '_{}__BaseGalleryItem'.format(cls.__name__)
        if getattr(cls, flag, None) is True or cls._meta.abstract:
            return []

        errors = []
        if cls.FORM_CLASS is None:
            errors.append(
                checks.Error(
                    "must define a FORM_CLASS attribute",
                    obj=cls,
                )
            )
        else:
            try:
                import_string(cls.FORM_CLASS)
            except ImportError:
                errors.append(
                    checks.Error(
                        "The value of FORM_CLASS refers to '%s', which does "
                        "not exists" % (
                            cls.FORM_CLASS
                        ),
                        obj=cls,
                    )
                )
        return errors

    @classmethod
    def _check_template_name(cls, **kwargs):
        flag = '_{}__BaseGalleryItem'.format(cls.__name__)
        if getattr(cls, flag, None) is True or cls._meta.abstract:
            return []

        errors = []
        if cls.TEMPLATE_NAME is None:
            errors.append(
                checks.Error(
                    "must define a TEMPLATE_NAME attribute",
                    obj=cls,
                )
            )
        return errors

    def save(self, *args, **kwargs):
        if not self.pk and not self.order:
            # добаление новых элементов в конец
            max_order = self.gallery.items.aggregate(
                order=functions.Coalesce(models.Max('order'), 0)
            )['order']
            self.order = max_order + 1
        super().save(*args, **kwargs)

    @cached_property
    def gallery_model(self):
        """
        Модель галереи.

        :rtype: T <= GalleryBase
        """
        return self.content_type.model_class()

    def as_dict(self):
        """
        Словарь, возвращаемый в виде JSON после загрузки файла.

        :return: dict
        """
        return {
            'id': self.pk,
            'gallery_id': self.object_id,
            'item_type': self.item_type,
        }

    def attach_to(self, gallery, item_type=None, commit=True):
        """
        Подключение элемента к галерее.
        Используется в случае динамического создания элементов галереи.

        :type gallery: GalleryBase
        :type item_type: str
        :type commit: bool
        """
        self.content_type = ContentType.objects.get_for_model(gallery, for_concrete_model=False)
        self.object_id = gallery.pk
        if item_type is None:
            for name, field in gallery.item_types.items():
                if field.model is type(self):
                    item_type = name
                    break
            else:
                raise ValueError('Gallery item type is not recognized')
        if item_type not in gallery.item_types:
            raise ValueError('Unsupported gallery item type: %s' % item_type)
        self.item_type = item_type
        if commit:
            self.save()


class GalleryFileItemBase(GalleryItemBase, UploadedFileBase):
    TEMPLATE_NAME = 'paper_uploads/gallery_item/file.html'

    file = models.FileField(_('file'), max_length=255, storage=upload_storage,
        upload_to=settings.GALLERY_FILES_UPLOAD_TO)
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(GalleryItemBase.Meta):
        abstract = True
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def as_dict(self):
        return {
            **super().as_dict(),
            'name': self.canonical_name,
            'url': self.file.url,
        }

    def pre_save_new_file(self):
        super().pre_save_new_file()
        if not self.pk and not self.display_name:
            self.display_name = self.name


class GalleryImageItemBase(GalleryItemBase, UploadedImageBase):
    TEMPLATE_NAME = 'paper_uploads/gallery_item/image.html'
    VARIATIONS = {}
    PREVIEW_VARIATIONS = settings.GALLERY_IMAGE_ITEM_PREVIEW_VARIATIONS

    file = models.FileField(_('file'), max_length=255, storage=upload_storage,
        upload_to=settings.GALLERY_IMAGES_UPLOAD_TO)

    class Meta(GalleryItemBase.Meta):
        abstract = True
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def get_variations(self):
        if not hasattr(self, '_variations_cache'):
            variations = dict(self.VARIATIONS, **self.PREVIEW_VARIATIONS)
            self._variations_cache = utils.build_variations(variations)
        return self._variations_cache

    def post_save_new_file(self):
        """
        При отложенной нарезке превью для админки режутся сразу,
        а остальное - потом.
        """
        if settings.RQ_ENABLED:
            preview_variations = tuple(self.PREVIEW_VARIATIONS.keys())
            self._recut_sync(names=preview_variations)
            self._postprocess(names=preview_variations)
            self.recut(names=tuple(
                name
                for name in self.get_variations()
                if name not in preview_variations
            ))
        else:
            self.recut()

    def as_dict(self):
        return {
            **super().as_dict(),
            'name': self.canonical_name,
            'url': self.file.url,
            'preview': loader.render_to_string('paper_uploads/gallery_item/preview/image.html', {
                'item': self,
                'preview_width': settings.GALLERY_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.GALLERY_ITEM_PREVIEW_HEIGTH,
            })
        }


class GalleryMetaclass(ModelBase):
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


class GalleryItemTypesDescriptor:
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        if owner is None:
            owner = type(instance)
        return OrderedDict(
            (field.name, field)
            for field in owner._local_item_type_fields
        )


class GalleryBase(SlaveModelMixin, metaclass=GalleryMetaclass):
    item_types = GalleryItemTypesDescriptor(name='item_types')
    items = GenericRelation(GalleryItemBase, for_concrete_model=False)
    created_at = models.DateTimeField(_('created at'), default=now, editable=False)

    class Meta:
        proxy = False
        abstract = True
        default_permissions = ()
        verbose_name = _('gallery')
        verbose_name_plural = _('galleries')

    @classmethod
    def _check_fields(cls, **kwargs):
        errors = super()._check_fields(**kwargs)
        for field in cls._local_item_type_fields:
            errors.extend(field.check(**kwargs))
        return errors

    @classmethod
    def guess_item_type(cls, file):
        # FIX: SVG не обрабатывается PIL, но имеет MIME-тип изображения
        filename, ext = posixpath.splitext(file.name)
        if ext.lower() == '.svg':
            return 'svg'

        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)
        basetype, subtype = mimetype.split('/', 1)
        if basetype == 'image':
            return 'image'
        return 'file'

    def get_items(self, item_type=None):
        if item_type is None:
            return self.items.order_by('order')
        if item_type not in self.item_types:
            raise ValueError('Unsupported gallery item type: %s' % item_type)
        return self.items.filter(item_type=item_type).order_by('order')

    def _recut_sync(self, names=(), using=DEFAULT_DB_ALIAS):
        recutable_items = tuple(
            name
            for name, field in self.item_types.items()
            if hasattr(field.model, 'recut')
        )
        for item in self.items.using(using).filter(item_type__in=recutable_items):
            item._recut_sync(names)

    def _recut_async(self, names=(), using=DEFAULT_DB_ALIAS):
        from django_rq.queues import get_queue
        queue = get_queue(settings.RQ_QUEUE_NAME)
        queue.enqueue_call(tasks.recut_gallery, kwargs={
            'app_label': self._meta.app_label,
            'model_name': self._meta.model_name,
            'object_id': self.pk,
            'names': names,
            'using': using,
        })

    def recut(self, names=None, using=DEFAULT_DB_ALIAS):
        if settings.RQ_ENABLED:
            self._recut_async(names, using=using)
        else:
            self._recut_sync(names, using=using)


# ==============================================================================


class GalleryFileItem(GalleryFileItemBase):
    FORM_CLASS = 'paper_uploads.forms.dialogs.gallery.GalleryFileDialog'

    preview = models.CharField(_('preview URL'), max_length=255, blank=True, editable=False)

    def as_dict(self):
        return {
            **super().as_dict(),
            'preview': loader.render_to_string('paper_uploads/gallery_item/preview/file.html', {
                'item': self,
                'preview_width': settings.GALLERY_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.GALLERY_ITEM_PREVIEW_HEIGTH,
            })
        }

    def pre_save_new_file(self):
        super().pre_save_new_file()
        icon = FILE_ICONS.get(self.extension, FILE_ICON_DEFAULT)
        self.preview = static('paper_uploads/dist/image/{}.svg'.format(icon))


class GallerySVGItem(GalleryFileItemBase):
    FORM_CLASS = 'paper_uploads.forms.dialogs.gallery.GalleryFileDialog'
    TEMPLATE_NAME = 'paper_uploads/gallery_item/svg.html'

    class Meta(GalleryItemBase.Meta):
        verbose_name = _('SVG-file')
        verbose_name_plural = _('SVG-files')

    def as_dict(self):
        return {
            **super().as_dict(),
            'preview': loader.render_to_string('paper_uploads/gallery_item/preview/svg.html', {
                'item': self,
                'preview_width': settings.GALLERY_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.GALLERY_ITEM_PREVIEW_HEIGTH,
            })
        }


class GalleryImageItem(GalleryImageItemBase):
    FORM_CLASS = 'paper_uploads.forms.dialogs.gallery.GalleryImageDialog'

    def get_variations(self):
        if not hasattr(self, '_variations_cache'):
            if self.VARIATIONS:
                variations = self.VARIATIONS.copy()
            elif 'gallery' in self.__dict__ and self.gallery:   # fix __getattr__ recursion
                variations = self.gallery.VARIATIONS.copy()
            else:
                # Получение вариаций из модели галереи для решения проблемы
                # с остаточными вариациями при удалением непустой галереи.
                gallery_method = getattr(self.content_type.model_class(), 'get_variations', None)
                if gallery_method is not None:
                    variations = gallery_method()
                else:
                    variations = {}

            variations.update(self.PREVIEW_VARIATIONS)
            self._variations_cache = utils.build_variations(variations)
        return self._variations_cache


class GalleryManager(models.Manager):
    """
    Из-за того, что все галереи являются прокси-моделями, запросы от имени
    любого из классов галереи затрагивает абсолютно все объекты галереи.
    С помощью этого менеджера можно работать только с галерями текущего типа.
    """
    def get_queryset(self):
        gallery_ct = ContentType.objects.get_for_model(self.model, for_concrete_model=False)
        return super().get_queryset().filter(gallery_content_type=gallery_ct)


class Gallery(GalleryBase):
    """
    Галерея, позволяющая хранить изображаения, SVG-файлы и файлы.
    """
    VARIATIONS = {}

    # поле, ссылающееся на одно из изображений галереи (для экономии SQL-запросов)
    cover = models.ForeignKey(GalleryImageItem, verbose_name=_('cover image'),
        null=True, editable=False, on_delete=models.SET_NULL)
    gallery_content_type = models.ForeignKey(ContentType, null=True,
        verbose_name=_('gallery type'), on_delete=models.SET_NULL, editable=False)

    objects = GalleryManager()

    class Meta:
        proxy = False   # явно указываем, что это не проски-модель

    def save(self, *args, **kwargs):
        if not self.gallery_content_type:
            self.gallery_content_type = ContentType.objects.get_for_model(self,
                for_concrete_model=False
            )
        super().save(*args, **kwargs)

    @classmethod
    def get_variations(cls):
        """
        Кэшируем конфиги вариаций для частичного решения проблемы с остаточными
        вариациями при удалением непустой галереи.
        """
        if not hasattr(cls, '_variations_cache'):
            variations = cls.VARIATIONS.copy()
            variations.update(cls.item_types['image'].model.PREVIEW_VARIATIONS)
            cls._variations_cache = variations
        return cls._variations_cache


class ImageGallery(Gallery):
    """
    Галерея, позволяющая хранить только изображения.
    """
    image = GalleryItemTypeField(GalleryImageItem)

    @classmethod
    def guess_item_type(cls, file):
        return 'image'

    @classmethod
    def get_validation(cls):
        return {
            **super().get_validation(),
            'acceptFiles': [
                'image/bmp',
                'image/gif',
                'image/jpeg',
                'image/pjpeg',
                'image/png',
                'image/tiff',
                'image/webp',
                'image/x-tiff',
                'image/x-windows-bmp',
            ],
        }
