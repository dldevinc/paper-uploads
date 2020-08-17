import hashlib
import os
from typing import Any, Dict, Iterable, Optional, Tuple

from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from PIL import Image
from variations.typing import Size
from variations.utils import prepare_image, replace_extension

from .. import helpers, signals
from ..conf import settings
from ..typing import FileLike
from ..variations import PaperVariation
from .mixins import BacklinkModelMixin, FileFieldProxyMixin, FileProxyMixin

__all__ = [
    'Resource',
    'FileResource',
    'FileFieldResource',
    'ImageFileResourceMixin',
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


class ResourceBase(models.Model):
    """
    Базовый класс ресурса.
    """

    name = models.CharField(
        _('name'),
        max_length=255,
        editable=False,
        help_text=_('human readable resource name'),
    )
    created_at = models.DateTimeField(_('created at'), default=now, editable=False)
    uploaded_at = models.DateTimeField(_('uploaded at'), default=now, editable=False)
    modified_at = models.DateTimeField(_('changed at'), auto_now=True, editable=False)

    class Meta:
        abstract = True
        default_permissions = ()

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self.name)

    def as_dict(self) -> Dict[str, Any]:
        """
        Представление объекта в виде словаря, конвертируемого в JSON.
        Служит для формирования виджета файла без перезагрузки страницы.
        """
        return {
            'id': self.pk,
            'name': self.name,
        }


class Resource(BacklinkModelMixin, ResourceBase):
    """
    Ресурс.
    Включает поля, позволяющие обратиться к модели и полю,
    через которые был создан ресурс.
    """

    class Meta(ResourceBase.Meta):
        abstract = True


class FileResource(FileProxyMixin, Resource):
    """
    Подкласс ресурса, представляющего файл.
    """

    BLOCK_SIZE = 4 * 1024 * 1024

    extension = models.CharField(
        _('extension'),
        max_length=32,
        editable=False,
        help_text=_('Lowercase, without leading dot'),
    )
    size = models.PositiveIntegerField(_('Size'), default=0, editable=False)
    content_hash = models.CharField(
        _('content hash'),
        max_length=64,
        editable=False,
        help_text=_('Hash of the contents of a file'),
    )

    class Meta(Resource.Meta):
        abstract = True

    def __str__(self):
        return self.get_basename()

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self.get_basename())

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'extension': self.extension,
            'size': self.size,
            'url': self.get_file_url(),
        }

    def get_hash(self, file: FileLike) -> str:
        """
        DropBox checksum realization.
        https://www.dropbox.com/developers/reference/content-hash
        """
        blocks = []
        file.seek(0)
        while True:
            data = file.read(self.BLOCK_SIZE)
            if not data:
                break
            blocks.append(hashlib.sha256(data).digest())
        return hashlib.sha256(b''.join(blocks)).hexdigest()

    def update_hash(self, file: FileLike) -> bool:
        old_hash = self.content_hash
        new_hash = self.get_hash(file)
        if new_hash and new_hash != old_hash:
            signals.content_hash_update.send(
                sender=type(self), instance=self, content_hash=new_hash
            )
            self.content_hash = new_hash
        return old_hash != new_hash

    def get_basename(self) -> str:
        """
        Человекопонятное имя файла.
        Не содержит суффикса, которое может быть добавлено файловым хранилищем.
        """
        return '{}.{}'.format(self.name, self.extension)

    def get_file(self) -> File:
        raise NotImplementedError

    def get_file_name(self) -> str:
        """
        Получение имени загруженного файла.
        В отличие от `self.name` это имя может содержать суффиксы, добавляемые
        файловым хранилищем.
        """
        raise NotImplementedError

    def get_file_size(self) -> int:
        """
        Получение размера загруженного файла.
        """
        raise NotImplementedError

    def get_file_url(self) -> str:
        """
        Получение ссылки на загруженный файл.
        """
        raise NotImplementedError

    def file_exists(self) -> bool:
        """
        Проверка существования файла.
        """
        raise NotImplementedError

    def attach_file(self, file: FileLike, name: str = None, **options):
        """
        Присоединение файла к экземпляру ресурса.
        В действительности, сохранение файла происходит в методе `_attach_file`.
        Не переопределяйте этот метод, если не уверены в том, что вы делаете.
        """
        if not isinstance(file, File):
            name = name or getattr(file, 'name', None)
            if name:
                name = os.path.basename(name)
            file = File(file, name=name)
        elif name:
            file.name = name

        prepared_file = self._prepare_file(file, **options)
        self.name = helpers.get_filename(prepared_file.name)
        self.extension = helpers.get_extension(prepared_file.name)

        signals.pre_attach_file.send(
            sender=type(self), instance=self, file=prepared_file, options=options
        )

        response = self._attach_file(prepared_file, **options)

        result_file = self.get_file()
        self.size = self.get_file_size()
        self.uploaded_at = now()
        self.modified_at = now()
        self.update_hash(result_file)

        signals.post_attach_file.send(
            sender=type(self),
            instance=self,
            file=result_file,
            options=options,
            response=response,
        )

    def _prepare_file(self, file: File, **options) -> File:
        """
        Подготовка файла к присоединению к модели.
        """
        return file

    def _attach_file(self, file: File, **options):
        raise NotImplementedError

    def rename_file(self, new_name: str, **options):
        """
        Переименование файла.
        В действительности, переименование файла происходит в методе `_rename_file`.
        Не переопределяйте этот метод, если не уверены в том, что вы делаете.
        """
        if not self.file_exists():
            raise FileNotFoundError

        old_name = self.get_file_name()

        name = helpers.get_filename(new_name)
        extension = helpers.get_extension(new_name)

        # если новое имя идентично прежнему - ничего не делаем
        if name == self.name and extension == self.extension:
            return

        signals.pre_rename_file.send(
            sender=type(self),
            instance=self,
            old_name=old_name,
            new_name=new_name,
            options=options,
        )

        response = self._rename_file(new_name, **options)

        # имя файла берем из переданного значения, а расширение - из результата
        # переименования, т.к. они могут быть модифицированы методом `_rename_file`.
        self.name = helpers.get_filename(new_name)
        self.extension = helpers.get_extension(self.get_file_name())

        signals.post_rename_file.send(
            sender=type(self),
            instance=self,
            old_name=old_name,
            new_name=new_name,
            options=options,
            response=response,
        )

    def _rename_file(self, new_name: str, **options):
        raise NotImplementedError

    def delete_file(self):
        """
        Удаление файла.
        В действительности, удаление файла происходит в методе `_delete_file`.
        Не переопределяйте этот метод, если не уверены в том, что вы делаете.
        """
        signals.pre_delete_file.send(sender=type(self), instance=self)
        self._delete_file()
        signals.post_delete_file.send(sender=type(self), instance=self)

    def _delete_file(self):
        raise NotImplementedError


class FileFieldResource(FileFieldProxyMixin, FileResource):
    """
    Подкласс файлового ресурса, доступ к которому осуществляется через Storage.
    """

    class Meta(FileResource.Meta):
        abstract = True

    def get_file(self) -> FieldFile:
        raise NotImplementedError

    def get_file_name(self) -> str:
        return self.get_file().name

    def get_file_size(self) -> int:
        return self.get_file().size

    def get_file_url(self) -> str:
        if not self.file_exists():
            raise FileNotFoundError
        return self.get_file().url

    def file_exists(self) -> bool:
        file = self.get_file()
        if not file:
            return False
        return file.storage.exists(file.name)

    def _attach_file(self, file: File, **options):
        self.get_file().save(file.name, file, save=False)

    def _rename_file(self, new_name: str, **options):
        with self.get_file().open() as fp:
            self.get_file().save(new_name, fp, save=False)

    def _delete_file(self):
        self.get_file().delete(save=False)


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
            **super().as_dict(),  # noqa
            'width': self.width,
            'height': self.height,
            'cropregion': self.cropregion,
            'title': self.title,
            'description': self.description,
        }

    def _prepare_file(self, file: File, **options) -> File:
        try:
            image = Image.open(file)
        except OSError:
            raise ValidationError(
                'File `%s` is not an image' % file.name
            )
        else:
            self.width, self.height = image.size

            # format extension
            file.name = replace_extension(file.name, format=image.format)
            root, ext = os.path.splitext(file.name)
            ext = ext.lstrip('.').lower()
            file.name = '.'.join([root, ext])

        return super()._prepare_file(file, **options)


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

    def __eq__(self, other):
        if hasattr(other, 'name'):
            return self.name == other.name
        return self.name == other

    def __hash__(self):
        return hash(self.name)

    def _require_file(self):
        if not self:
            raise ValueError(
                "Variation '%s' has no file associated with it." % self.variation_name
            )

    def _get_file(self) -> File:
        self._require_file()
        if getattr(self, '_file', None) is None:
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
        self._require_file()
        return self.storage.path(self.name)

    @property
    def url(self) -> str:
        self._require_file()
        return self.storage.url(self.name)

    @property
    def size(self) -> int:
        self._require_file()
        return self.storage.size(self.name)

    def exists(self) -> bool:
        if not self:
            return False
        return self.storage.exists(self.name)

    def open(self, mode: str = 'rb'):
        self._require_file()
        if getattr(self, '_file', None) is None:
            self.file = self.storage.open(self.name, mode)
        else:
            self.file.open(mode)
        return self

    # open() doesn't alter the file's contents, but it does reset the pointer
    open.alters_data = True  # noqa

    def delete(self):
        if not self:
            return

        if hasattr(self, '_file'):
            self.close()
            del self.file

        self.storage.delete(self.name)
        self.name = None

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


class VersatileImageResourceMixin(ImageFileResourceMixin):
    """
    Подкласс файлового ресурса для вариативного изображения.
    """

    # класс файла вариации
    variation_class = VariationFile

    # флаг, запускающий нарезку вариаций после сохранения экземпляра модели в БД
    need_recut = False

    class Meta(ImageFileResourceMixin.Meta):
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # нельзя использовать `_reset_variation_files`, т.к. он обращается
        # к `get_variations`, что может быть неопределено для элементов коллекций.
        self._variation_files_cache = {}

        # инициализация аттрибутов вариаций для уже загруженных файлов
        if self.pk:
            self._setup_variation_files()

    def __getattr__(self, item):
        # реализация-заглушка, чтобы PyCharm не ругался на атрибуты-вариации
        raise AttributeError(
            "{!r} object has no attribute {!r}".format(self.__class__.__name__, item)
        )

    def _reset_variation_files(self):
        self._variation_files_cache = {}
        for vname in self.get_variations():
            if vname in self.__dict__:
                del self.__dict__[vname]

    def _setup_variation_files(self):
        self._variation_files_cache.clear()
        for vname, vfile in self.variation_files():
            self.__dict__[vname] = vfile

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.need_recut:
            self.need_recut = False
            if settings.RQ_ENABLED:
                self.recut_async()
            else:
                self.recut()

    def attach_file(self, file: FileLike, name: str = None, **options):
        super().attach_file(file, name=name, **options)
        self.need_recut = True
        self._setup_variation_files()

    def _delete_file(self):
        for vname, vfile in self.variation_files():
            if vfile is not None:
                vfile.delete()
        super()._delete_file()  # noqa
        self._reset_variation_files()

    def _rename_file(self, new_name: str, **options):
        super()._rename_file(new_name)  # noqa
        self.recut()
        self._setup_variation_files()

    def get_variations(self) -> Dict[str, PaperVariation]:
        raise NotImplementedError

    def variation_files(self) -> Iterable[Tuple[str, VariationFile]]:
        if not self._variation_files_cache:
            if not self.get_file():
                return

            self._variation_files_cache = {
                vname: self.get_variation_file(vname) for vname in self.get_variations()
            }
        yield from self._variation_files_cache.items()

    def get_variation_file(self, variation_name: str) -> VariationFile:
        return self.variation_class(instance=self, variation_name=variation_name)

    def calculate_max_size(self, source_size: Size) -> Optional[Tuple[int, int]]:
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
        return None

    def _save_variation(self, name: str, variation: PaperVariation, image: Image):
        """
        Запись изображения в файловое хранилище
        """
        variation_file = self.get_variation_file(name)
        with variation_file.open('wb') as fp:
            variation.save(image, fp)

    def recut(self, names: Iterable[str] = ()):
        """
        Нарезка вариаций.
        Можно указать имена конкретных вариаций в параметре `names`.
        """
        if not self.file_exists():
            raise FileNotFoundError

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
                self._save_variation(name, variation, image)

                signals.variation_created.send(
                    sender=type(self), instance=self, file=self.get_variation_file(name)
                )

    def recut_async(self, names: Iterable[str] = ()):
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
                'names': names,
            },
        )

    @classmethod
    def _recut_task(
        cls,
        app_label: str,
        model_name: str,
        object_id: int,
        using: str,
        names: Iterable[str],
    ):
        """
        Задача для django-rq.
        Вызывает `recut()` экземпляра в отдельном процессе.
        """
        instance = helpers.get_instance(app_label, model_name, object_id, using=using)
        instance.recut(names)
