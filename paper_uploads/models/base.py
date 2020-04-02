import hashlib
import io
import os
from typing import IO, Any, Dict, Iterable, Optional, Sequence, Tuple, Type, Union

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.files import File
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from PIL import Image
from variations.utils import prepare_image

from .. import signals, utils
from ..conf import settings
from ..logging import logger
from ..variations import PaperVariation

__all__ = [
    'Resource',
    'HashableResourceMixin',
    'FileResource',
    'FileFieldResource',
    'PostprocessableFileFieldResource',
    'ReverseFieldModelMixin',
    'ReadonlyFileProxyMixin',
    'ImageFileResourceMixin',
    'ImageFieldResourceMixin',
    'VariationFile',
    'VersatileImageResourceMixin',
]


class Permissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('upload', 'Can upload files'),
            ('change', 'Can change files'),
            ('delete', 'Can delete files'),
        )


class Resource(models.Model):
    """
    Базовый класс ресурса, который может хранить модуль.
    """

    name = models.CharField(_('name'), max_length=255, editable=False)
    created_at = models.DateTimeField(_('created at'), default=now, editable=False)
    uploaded_at = models.DateTimeField(_('uploaded at'), default=now, editable=False)
    modified_at = models.DateTimeField(_('changed at'), auto_now=True, editable=False)

    class Meta:
        abstract = True
        default_permissions = ()

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{}('{}')".format(
            type(self).__name__,
            self.name
        )

    def as_dict(self) -> Dict[str, Any]:
        """
        Представление объекта в виде словаря, конвертируемого в JSON.
        Служит для формирования виджета файла без перезагрузки страницы.
        """
        return {
            'id': self.pk,
            'name': self.name,
        }


class HashableResourceMixin(Resource):
    """
    Подкласс ресурса, который содержит хэш своего контента.
    Хэш может быть использован для поиска дубликатов и других целей.
    """

    hash = models.CharField(
        _('hash'),
        max_length=40,
        editable=False,
        help_text=_('SHA-1 checksum of a resource'),
    )

    class Meta(Resource.Meta):
        abstract = True

    def get_hash(self, file: File) -> str:
        raise NotImplementedError

    def update_hash(self, file: File) -> bool:
        """
        :return: updated
        """
        new_hash = self.get_hash(file)
        if new_hash and new_hash != self.hash:
            signals.hash_updated.send(type(self), instance=self, hash=new_hash)
            self.hash = new_hash
            return True
        return False


class FileResource(HashableResourceMixin):
    """
    Подкласс ресурса, представляющего файл.
    """

    extension = models.CharField(
        _('extension'),
        max_length=32,
        editable=False,
        help_text=_('Lowercase, without leading dot'),
    )
    size = models.PositiveIntegerField(_('size'), default=0, editable=False)

    class Meta(HashableResourceMixin.Meta):
        abstract = True

    def __str__(self):
        return self.get_basename()

    def __repr__(self):
        return "{}('{}')".format(
            type(self).__name__,
            self.get_basename()
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'extension': self.extension,
            'size': self.size,
            'url': self.get_file_url(),
        }

    def get_hash(self, file: File) -> str:
        sha1 = hashlib.sha1()
        if file.multiple_chunks():
            for chunk in file.chunks():
                sha1.update(chunk)
        else:
            sha1.update(file.read())
        return sha1.hexdigest()

    def get_basename(self) -> str:
        return '{}.{}'.format(self.name, self.extension)

    def get_file(self) -> File:
        raise NotImplementedError

    def get_file_name(self) -> str:
        """
        Получение имени загруженного файла.
        """
        raise NotImplementedError

    def get_file_url(self) -> str:
        """
        Получение ссылки на загруженный файл.
        """
        raise NotImplementedError

    def is_file_exists(self) -> bool:
        """
        Проверка существования файла.
        """
        raise NotImplementedError

    def attach_file(self, file: Union[File, IO], name: str = None, **options):
        if not isinstance(file, File):
            name = name or getattr(file, 'name', None)
            if name:
                name = os.path.basename(name)
            file = File(file, name=name)

        # запоминаем оригинальное имя файла, т.к. финальное имя может
        # включать в себя суффикс от Django Storage или другого источника.
        basename = os.path.basename(file.name)
        self.name, _ = os.path.splitext(basename)

        self.size = file.size
        self.uploaded_at = now()
        self.modified_at = now()
        self.update_hash(file)
        file.seek(0)

        signals.pre_attach_file.send(
            type(self), instance=self, file=file, options=options
        )
        response = self._attach_file(file, **options)
        signals.post_attach_file.send(type(self), instance=self, response=response)

        # запоминаем расширение файла после загрузки файла, т.к. при загрузке
        # оно может быть отформатировано.
        basename = os.path.basename(self.get_file_name())
        _, extension = os.path.splitext(basename)
        self.extension = extension.lower().lstrip('.')

    def _attach_file(self, file: File, **options):
        raise NotImplementedError

    def rename_file(self, new_name: str):
        self.name = new_name
        signals.pre_rename_file.send(type(self), instance=self, new_name=new_name)
        self._rename_file(new_name)
        signals.post_rename_file.send(type(self), instance=self, new_name=new_name)

    def _rename_file(self, new_name: str):
        raise NotImplementedError

    def delete_file(self):
        signals.pre_delete_file.send(type(self), instance=self)
        self._delete_file()
        signals.post_delete_file.send(type(self), instance=self)

    def _delete_file(self):
        raise NotImplementedError


class FileFieldResource(FileResource):
    """
    Подкласс файлового ресурса, доступ к которому осуществляется через Storage.
    """

    class Meta(FileResource.Meta):
        abstract = True

    def get_file(self) -> FieldFile:
        raise NotImplementedError

    def get_file_name(self) -> str:
        return self.get_file().name

    def get_file_url(self) -> str:
        return self.get_file().url

    def is_file_exists(self) -> bool:
        file = self.get_file()
        if file is None or not file.name:
            return False
        return file.storage.exists(file.name)

    def _attach_file(self, file: File, **options):
        self.get_file().save(file.name, file, save=False)

    def _rename_file(self, new_name: str):
        name = '.'.join((new_name, self.extension))
        with self.get_file().open() as fp:
            self.get_file().save(name, fp, save=False)

    def _delete_file(self):
        self.get_file().delete(save=False)


class PostprocessableFileFieldResource(FileFieldResource):
    """
    Подкласс файлового ресурса, который может быть обработан локальными утилитами.
    Используемый Django Storage должен быть подклассом FileSystemStorage.
    """

    # флаг, запускающий постобработку после сохранения экземпляра модели в БД
    need_postprocess = False

    class Meta(FileFieldResource.Meta):
        abstract = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.need_postprocess:
            self.need_postprocess = False
            kwargs = self.get_postprocess_kwargs()
            if settings.RQ_ENABLED:
                self.postprocess_async(**kwargs)
            else:
                self.postprocess(**kwargs)

    def attach_file(self, file: Union[File, IO], name: str = None, **options):
        super().attach_file(file, name=name, **options)
        self.need_postprocess = True

    def postprocess(self, **kwargs):
        """
        Метод постобработки загруженного файла.
        """
        raise NotImplementedError

    def get_postprocess_kwargs(self) -> Dict[str, Any]:
        """
        Возвращает дополнительные аргументы для метода `postprocess()`.
        """
        return {}

    def postprocess_async(self, **kwargs):
        """
        Добавление задачи постобработки в django-rq.
        """
        from django_rq.queues import get_queue

        queue = get_queue(settings.RQ_QUEUE_NAME)
        queue.enqueue_call(
            self._postprocess_task,
            kwargs={
                'app_label': self._meta.app_label,
                'model_name': self._meta.model_name,
                'object_id': self.pk,
                'using': self._state.db,
                **kwargs,
            },
        )

    @classmethod
    def _postprocess_task(
        cls, app_label: str, model_name: str, object_id: int, using: str, **kwargs
    ):
        """
        Задача для django-rq.
        Вызывает `postprocess()` экземпляра в отдельном процессе.
        """
        instance = utils.get_instance(app_label, model_name, object_id, using=using)
        instance.postprocess(**kwargs)


class ImageFileResourceMixin(models.Model):
    """
    Подкласс файлового ресурса для изображений
    """

    title = models.CharField(
        _('title'),
        max_length=255,
        blank=True,
        help_text=_(
            'The title is being used as a tooltip when the user hovers the mouse over the image'
        ),
    )
    description = models.CharField(
        _('description'),
        max_length=255,
        blank=True,
        help_text=_(
            'This text will be used by screen readers, search engines, or when the image cannot be loaded'
        ),
    )
    width = models.PositiveSmallIntegerField(_('width'), default=0, editable=False)
    height = models.PositiveSmallIntegerField(_('height'), default=0, editable=False)
    cropregion = models.CharField(
        _('crop region'), max_length=24, blank=True, editable=False
    )

    class Meta:
        abstract = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'width': self.width,
            'height': self.height,
            'cropregion': self.cropregion,
            'title': self.title,
            'description': self.description,
        }


class ImageFieldResourceMixin(ImageFileResourceMixin):
    """
    Подкласс файлового ресурса изображения, доступ к которому осуществляется через Storage.
    """

    class Meta(ImageFileResourceMixin.Meta):
        abstract = True

    def attach_file(self, file: Union[File, IO], name: str = None, **options):
        super().attach_file(file, name=name, **options)
        with self.get_file().open():
            try:
                image = Image.open(self.get_file())
            except OSError:
                raise ValidationError('`%s` is not an image' % self.get_basename())
            else:
                self.width, self.height = image.size


class VariationFile(File):
    """
    Файл вариации изображения
    """

    def __init__(self, instance, variation_name):
        self.instance = instance
        self.variation_name = variation_name
        self.storage = instance.get_file().storage
        filename = self.variation.get_output_filename(instance.get_file_name())
        super().__init__(None, filename)

    def _get_file(self) -> File:
        if not hasattr(self, '_file') or self._file is None:
            self._file = self.storage.open(self.name, 'rb')
        return self._file

    def _set_file(self, file: File):
        self._file = file

    def _del_file(self):
        del self._file

    file = property(_get_file, _set_file, _del_file)

    @property
    def variation(self) -> PaperVariation:
        variations = self.instance.get_variations()
        return variations[self.variation_name]

    @property
    def path(self) -> str:
        return self.storage.path(self.name)

    @property
    def url(self) -> str:
        return self.storage.url(self.name)

    @property
    def size(self) -> int:
        return self.storage.size(self.name)

    def exists(self) -> bool:
        return self.storage.exists(self.name)

    def open(self, mode: str = 'rb'):
        if hasattr(self, '_file') and self._file is not None:
            self.file.open(mode)
        else:
            self.file = self.storage.open(self.name, mode)

    # open() doesn't alter the file's contents, but it does reset the pointer
    open.alters_data = True

    def delete(self):
        self.storage.delete(self.name)

    delete.alters_data = True

    @property
    def closed(self) -> bool:
        file = getattr(self, '_file', None)
        return file is None or file.closed

    def close(self):
        file = getattr(self, '_file', None)
        if file is not None:
            file.close()

    @property
    def width(self) -> int:
        return self._get_image_dimensions()[0]

    @property
    def height(self) -> int:
        return self._get_image_dimensions()[1]

    def _get_image_dimensions(self):
        if not hasattr(self, '_dimensions_cache'):
            dimensions = self.variation.get_output_size(
                (self.instance.width, self.instance.height)
            )
            self._dimensions_cache = dimensions
        return self._dimensions_cache


class VersatileImageResourceMixin(ImageFieldResourceMixin):
    """
    Подкласс файлового ресурса вариативного изображения, доступ к которому
    осуществляется через Storage.
    Изображение и его вариации могут быть подвержены постобработке.
    """

    # флаг, запускающий нарезку вариаций после сохранения экземпляра модели в БД
    need_recut = False

    class Meta(ImageFieldResourceMixin.Meta):
        abstract = True

    def __init__(self, *args, **kwargs):
        self._variations_attached = False
        self._variation_files_cache = {}
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        if not name.startswith('_') and not self._variations_attached:
            for vname, vfile in self.variation_files():
                setattr(self, vname, vfile)
            self._variations_attached = True
            if name in self.get_variations():
                return getattr(self, name)
        raise AttributeError('module {!r} has no attribute {!r}'.format(
            __name__,
            name
        ))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.need_recut:
            self.need_recut = False
            kwargs = self.get_recut_kwargs()
            if settings.RQ_ENABLED:
                self.recut_async(**kwargs)
            else:
                self.recut(**kwargs)

    def attach_file(self, file: Union[File, IO], name: str = None, **options):
        super().attach_file(file, name=name, **options)
        self.need_recut = True
        self._variation_files_cache.clear()

    def _delete_file(self):
        for vname, vfile in self.variation_files():
            if vfile is not None:
                vfile.delete()
        super()._delete_file()

    def _rename_file(self, new_name: str):
        super()._rename_file(new_name)
        self.recut()
        self._variation_files_cache.clear()

    def get_variations(self) -> Dict[str, PaperVariation]:
        raise NotImplementedError

    def variation_files(self) -> Iterable[Tuple[str, Union[VariationFile, None]]]:
        for variation_name in self.get_variations():
            yield variation_name, self.get_variation_file(variation_name)

    def get_variation_file(self, variation_name: str) -> Optional[VariationFile]:
        """
        Если оригинального изображения нет - возвращает None
        """
        if not self.get_file():
            return

        cache = self._variation_files_cache
        if variation_name in cache:
            variation_file = cache[variation_name]
        else:
            variation_file = VariationFile(instance=self, variation_name=variation_name)
            cache[variation_name] = variation_file
        return variation_file

    def calculate_max_size(self, source_size: Sequence[int]) -> Optional[Tuple[int, int]]:
        """
        Вычисление максимально возможных значений ширины и высоты изображения
        среди всех вариаций, чтобы передать их в Image.draft().
        """
        max_width = 0
        max_height = 0
        for name, variation in self.get_variations().items():
            size = variation.get_output_size(source_size)
            max_width = max(max_width, size[0])
            max_height = max(max_height, size[1])
        if max_width and max_height:
            return max_width, max_height

    def postprocess_variation(self, file: VariationFile, variation: PaperVariation):
        """
        Метод постобработки вариации
        """
        raise NotImplementedError

    def recut(self, names: Iterable[str] = (), **kwargs):
        """
        Нарезка вариаций.
        Можно указать имена конкретных вариаций в параметре `names`.
        """
        file = self.get_file()
        if not file:
            return

        with file.open() as source:
            img = Image.open(source)
            draft_size = self.calculate_max_size(img.size)
            img = prepare_image(img, draft_size=draft_size)

            for name, variation in self.get_variations().items():
                if names and name not in names:
                    continue

                image = variation.process(img)

                # не все удаленные storage поддерживают запись в открытые файлы,
                # поэтому используем метод save и буфер.
                buffer = io.BytesIO()
                variation.save(image, buffer)
                buffer.seek(0)

                variation_filename = variation.get_output_filename(self.get_file_name())
                file.storage.save(variation_filename, buffer)

                variation_file = self.get_variation_file(name)
                if variation_file is None:
                    raise RuntimeError("variation file for '{}' does not exist".format(name))

                self.postprocess_variation(variation_file, variation)

    def get_recut_kwargs(self) -> Dict[str, Any]:
        """
        Возвращает дополнительные аргументы для метода `recut()`.
        """
        return {}

    def recut_async(self, **kwargs):
        """
        Добавление задачи нарезки вариаций в django-rq.
        """
        from django_rq.queues import get_queue

        queue = get_queue(settings.RQ_QUEUE_NAME)
        queue.enqueue_call(
            self._recut_task,
            kwargs={
                'app_label': self._meta.app_label,
                'model_name': self._meta.model_name,
                'object_id': self.pk,
                'using': self._state.db,
                **kwargs,
            },
        )

    @classmethod
    def _recut_task(
        cls, app_label: str, model_name: str, object_id: int, using: str, **kwargs
    ):
        """
        Задача для django-rq.
        Вызывает `recut()` экземпляра в отдельном процессе.
        """
        instance = utils.get_instance(app_label, model_name, object_id, using=using)
        instance.recut(**kwargs)


class ReverseFieldModelMixin(models.Model):
    """
    Миксина, позволяющая обратиться к полю модели, которое ссылается
    на текущий объект.
    """

    owner_app_label = models.CharField(max_length=100, editable=False)
    owner_model_name = models.CharField(max_length=100, editable=False)
    owner_fieldname = models.CharField(max_length=255, editable=False)

    class Meta:
        abstract = True

    def get_owner_model(self) -> Optional[Type[models.Model]]:
        if not self.owner_app_label or not self.owner_model_name:
            return

        try:
            return apps.get_model(self.owner_app_label, self.owner_model_name)
        except LookupError:
            logger.debug(
                "Not found model: %s.%s" % (self.owner_app_label, self.owner_model_name)
            )

    def get_owner_field(self) -> Optional[models.Field]:
        owner_model = self.get_owner_model()
        if owner_model is None:
            return

        try:
            return owner_model._meta.get_field(self.owner_fieldname)
        except FieldDoesNotExist:
            logger.debug(
                "Not found field '%s' in model %s.%s"
                % (self.owner_app_label, self.owner_model_name, self.owner_fieldname)
            )


class ReadonlyFileProxyMixin:
    """
    Проксирование некоторых свойств файла (только для чтения) на уровень модели
    """

    closed = property(lambda self: self.get_file().closed)
    path = property(lambda self: self.get_file().path)
    read = property(lambda self: self.get_file().read)
    seek = property(lambda self: self.get_file().seek)
    tell = property(lambda self: self.get_file().tell)
    url = property(lambda self: self.get_file().url)

    def __enter__(self):
        return self.get_file()

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def open(self, mode='rb'):
        return self.get_file().open(mode)

    open.alters_data = True

    def close(self):
        self.get_file().close()
