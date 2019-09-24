import os
import base64
import filetype
from PIL import Image
from typing import Dict, Iterator, Tuple, Iterable, Optional, Any, Sequence
from django.db import models
from django.core.files import File
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError, SuspiciousFileOperation
from variations.variation import Variation
from variations.utils import prepare_image
from .base import UploadedFileBase, SlaveModelMixin
from ..storage import upload_storage
from ..conf import settings, PROXY_FILE_ATTRIBUTES
from .. import utils
from .. import tasks


class VariationFile(File):
    def __init__(self, instance, variation_name):
        self.instance = instance
        self.variation_name = variation_name
        self.storage = instance.file.storage
        filename = utils.get_variation_filename(instance.file.name, variation_name, self.variation)
        super().__init__(None, filename)

    def _get_file(self):
        if not hasattr(self, '_file') or self._file is None:
            self._file = self.storage.open(self.name, 'rb')
        return self._file

    def _set_file(self, file):
        self._file = file

    def _del_file(self):
        del self._file

    file = property(_get_file, _set_file, _del_file)

    @property
    def variation(self) -> Variation:
        variations = self.instance.get_variations()
        return variations[self.variation_name]

    @property
    def path(self) -> str:
        return self.storage.path(self.name)

    @property
    def url(self) -> str:
        return self.storage.url(self.name)

    def data_uri(self) -> str:
        parts = ['data:']

        self.open()
        data = self.read()
        self.close()

        # default mimetypes library does not recognize webp :(
        mimetype = filetype.guess_mime(data)
        parts.append(mimetype)

        encoded_data = base64.encodebytes(data).decode().strip()
        parts.extend([';base64,', encoded_data])
        return ''.join(parts)
    data_uri.alters_data = True

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


class UploadedImageBase(UploadedFileBase):
    alt = models.CharField(_('alternate text'), max_length=255, blank=True,
        help_text=_('This text will be used by screen readers, search engines, or when the image cannot be loaded'))
    title = models.CharField(_('title'), max_length=255, blank=True,
        help_text=_('The title is used as a tooltip when the user hovers the mouse over the image'))
    width = models.PositiveSmallIntegerField(_('width'), default=0, editable=False)
    height = models.PositiveSmallIntegerField(_('height'), default=0, editable=False)
    cropregion = models.CharField(_('crop region'), max_length=24, blank=True, editable=False)

    class Meta(UploadedFileBase.Meta):
        abstract = True

    def __getattr__(self, item):
        if item in PROXY_FILE_ATTRIBUTES:
            return getattr(self.file, item)
        if not item.startswith('_'):
            if item in self.get_variations():
                return self.get_variation_file(item)
        raise AttributeError(
            "'%s' object has no attribute '%s'" % (self.__class__.__name__, item)
        )

    def pre_save_new_file(self):
        file_closed = self.file.closed
        try:
            image = Image.open(self.file)
        except OSError:
            raise ValidationError('Not an Image')

        self.width, self.height = image.size

        # оставляем файл в первоначальном состоянии
        if file_closed:
            image.close()

        super().pre_save_new_file()

    def post_save_new_file(self):
        """
        При сохранении нового файла, автоматически создаем для него все вариации.
        """
        super().post_save_new_file()
        self.recut()

    def post_delete_callback(self):
        """
        При удалении экземпляра, автоматически удаляем все вариации.
        """
        for name, file in self.get_variation_files():
            file.delete()
        super().post_delete_callback()

    def get_variations(self) -> Dict[str, Variation]:
        """
        Получение объектов вариаций
        """
        raise NotImplementedError

    def get_variation_files(self) -> Iterator[Tuple[str, VariationFile]]:
        """
        Итератор по вариациям файла.
        """
        for variation_name in self.get_variations():
            yield variation_name, self.get_variation_file(variation_name)

    def get_variation_file(self, variation_name: str) -> Optional[VariationFile]:
        """
        Получение экземпляра VariationFile, представляющего файл вариации.
        """
        if not self.file:
            return

        variation_cache_name = '_file_{}'.format(variation_name)
        variation_cache = getattr(self, variation_cache_name, None)
        if variation_cache is None:
            variation_cache = VariationFile(
                instance=self,
                variation_name=variation_name
            )
            setattr(self, variation_cache_name, variation_cache)
        return variation_cache

    def get_draft_size(self, source_size: Sequence[int]) -> Tuple[int, int]:
        """
        Вычисление максимально возможных значений ширины и высоты для всех
        вариаций, чтобы передать их в Image.draft().
        """
        max_width = 0
        max_height = 0
        for name, variation in self.get_variations().items():
            size = variation.get_output_size(source_size)
            max_width = max(max_width, size[0])
            max_height = max(max_height, size[1])
        if max_width and max_height:
            return max_width, max_height

    def _recut_sync(self, names: Iterable[str] = ()):
        """
        Перенарезка указанных вариаций.
        Если конкретные вариации не указаны, перенарезаны будут все.
        """
        if not self.file:
            return

        with self.file.open() as source:
            img = Image.open(source)
            img = prepare_image(img,
                draft_size=self.get_draft_size(img.size)
            )
            for name, variation in self.get_variations().items():
                if names and name not in names:
                    continue

                image = variation.process(img)
                variation_path = utils.get_variation_filename(self.file.name, name, variation)
                with self.file.storage.open(variation_path, 'wb+') as fp:
                    variation.save(image, fp)
                    utils.postprocess_variation(self.file.name, name, variation)

    def _recut_async(self, names: Iterable[str] = ()):
        from django_rq.queues import get_queue
        queue = get_queue(settings.RQ_QUEUE_NAME)
        queue.enqueue_call(tasks.recut_image, kwargs={
            'app_label': self._meta.app_label,
            'model_name': self._meta.model_name,
            'object_id': self.pk,
            'names': names,
            'using': self._state.db,
        })

    def recut(self, names: Iterable[str] = None):
        if settings.RQ_ENABLED:
            self._recut_async(names)
        else:
            self._recut_sync(names)


class VariationalFileField(models.FileField):
    """
    Из-за того, что вариация может самостоятельно установить свой формат,
    возможна ситуация, когда вариации одного изображения перезапишут вариации
    другого. Например, когда загружаются файлы, отличающиеся только расширением.
    Поэтому мы проверяем все имена будующих вариаций на существование, чтобы
    не допустить перезапись.
    """
    def variation_collapse(self, instance, name):
        if self.storage.exists(name):
            return True

        for vname, variation in instance.get_variations().items():
            variation_filename = utils.get_variation_filename(name, vname, variation)
            if self.storage.exists(variation_filename):
                return True
        return False

    def generate_filename(self, instance, filename):
        name = super().generate_filename(instance, filename)

        max_length = self.max_length
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        while self.variation_collapse(instance, name) or (max_length and len(name) > max_length):
            name = os.path.join(dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext))
            if max_length is None:
                continue
            # Truncate file_root if max_length exceeded.
            truncation = len(name) - max_length
            if truncation > 0:
                file_root = file_root[:-truncation]
                # Entire file_root was truncated in attempt to find an available filename.
                if not file_root:
                    raise SuspiciousFileOperation(
                        'Storage can not find an available filename for "%s". '
                        'Please make sure that the corresponding file field '
                        'allows sufficient "max_length".' % name
                    )
                name = os.path.join(dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext))
        return name


class UploadedImage(UploadedImageBase, SlaveModelMixin):
    file = VariationalFileField(_('file'), max_length=255, upload_to=settings.IMAGES_UPLOAD_TO, storage=upload_storage)

    class Meta(UploadedImageBase.Meta):
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def get_variations(self) -> Dict[str, Variation]:
        if not hasattr(self, '_variations_cache'):
            owner_field = self.get_owner_field()
            if owner_field is not None:
                self._variations_cache = getattr(owner_field, 'variations')
            else:
                return {}
        return self._variations_cache

    @classmethod
    def get_validation(cls) -> Dict[str, Any]:
        return {
            **super().get_validation(),
            'acceptFiles': 'image/*',
        }

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'width': self.width,
            'height': self.height,
            'file_info': '({ext}, {width}x{height}, {size})'.format(
                ext=self.extension,
                width=self.width,
                height=self.height,
                size=filesizeformat(self.size)
            )
        }
