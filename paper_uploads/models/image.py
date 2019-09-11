import os
import base64
import filetype
import posixpath
import subprocess
from PIL import Image
from django.db import models
from django.core.files import File
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.contrib.contenttypes.models import ContentType
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
        filename = instance.get_variation_path(variation_name)
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
    def variation(self):
        variations = self.instance.get_variations()
        return variations[self.variation_name]

    @property
    def path(self):
        return self.storage.path(self.name)

    @property
    def url(self):
        return self.storage.url(self.name)

    def data_uri(self):
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
    def size(self):
        return self.storage.size(self.name)

    def exists(self):
        return self.storage.exists(self.name)

    def open(self, mode='rb'):
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
    def closed(self):
        file = getattr(self, '_file', None)
        return file is None or file.closed

    def close(self):
        file = getattr(self, '_file', None)
        if file is not None:
            file.close()

    @property
    def width(self):
        return self._get_image_dimensions()[0]

    @property
    def height(self):
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
        self.recut()

    def post_delete_callback(self):
        """
        При удалении экземпляра, автоматически удаляем все вариации.
        """
        for vname, vfile in self.get_variation_files():
            vfile.delete()
        super().post_delete_callback()

    def get_variations(self):
        """
        Получение вариаций из экземпляра поля, ссылающегося на файл.

        :rtype: dict[str, variations.variation.Variation]
        """
        raise NotImplementedError

    def get_variation_files(self):
        """
        Итератор по файлам вариаций.

        :rtype: collections.Iterable[(str, VariationFile)]
        """
        for variation_name in self.get_variations():
            yield variation_name, self.get_variation_file(variation_name)

    def get_variation_file(self, variation_name):
        """
        Получение экземпляра VariationFile, представляющего файл вариации.

        :type variation_name: str
        :rtype: VariationFile
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

    def get_variation_path(self, variation_name):
        """
        Получение пути к файлу вариации.

        :type variation_name: str
        :rtype: str
        """
        variations = self.get_variations()
        variation = variations[variation_name]

        root, basename = posixpath.split(self.file.name)
        filename, ext = posixpath.splitext(basename)
        filename = posixpath.extsep.join((filename, variation_name))
        basename = ''.join((filename, ext))
        path = posixpath.join(root, basename)
        return variation.replace_extension(path)

    def get_draft_size(self, source_size):
        """
        Вычисление максимально возможных значений ширины и высоты для всех
        вариаций, чтобы передать их в Image.draft().

        :type source_size: list | tuple
        :rtype: tuple
        """
        max_width = 0
        max_height = 0
        for name, variation in self.get_variations().items():
            size = variation.get_output_size(source_size)
            max_width = max(max_width, size[0])
            max_height = max(max_height, size[1])
        if max_width and max_height:
            return max_width, max_height

    def _recut_sync(self, names=()):
        """
        Перенарезка указанных вариаций.
        Если конкретные вариации не указаны, перенарезаны будут все.

        :type names: list | tuple
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
                path = self.get_variation_path(name)
                with self.file.storage.open(path, 'wb+') as fp:
                    variation.save(image, fp)
        self._postprocess(names)

    def _recut_async(self, names=()):
        from django_rq.queues import get_queue
        queue = get_queue(settings.RQ_QUEUE_NAME)
        queue.enqueue_call(tasks.recut_image, kwargs={
            'app_label': self._meta.app_label,
            'model_name': self._meta.model_name,
            'object_id': self.pk,
            'names': names,
            'using': self._state.db,
        })

    def _postprocess(self, names=()):
        for name, variation in self.get_variations().items():
            if names and name not in names:
                continue

            path = self.get_variation_path(name)
            full_path = upload_storage.path(path)
            if not os.path.exists(full_path):
                utils.logger.warning('File not found: {}'.format(path))
                continue

            output_format = variation.output_format(path)
            default_postprocess_opts = getattr(settings, 'POSTPROCESS_{}'.format(output_format), {})
            user_format_opts = variation.extra_context.get(output_format, {})
            user_postprocess_opts = user_format_opts.get('postprocess', {})

            if user_postprocess_opts is None:
                # компрессия явно запрещена
                continue
            elif 'command' in user_postprocess_opts:
                postprocess_cmd = user_postprocess_opts['command']
            elif 'COMMAND' in default_postprocess_opts:
                postprocess_cmd = default_postprocess_opts['COMMAND']
            else:
                # нет настроек для данного формата
                continue

            if 'arguments' in user_postprocess_opts:
                postprocess_args = user_postprocess_opts['arguments']
            elif 'ARGUMENTS' in default_postprocess_opts:
                postprocess_args = default_postprocess_opts['ARGUMENTS']
            else:
                postprocess_args = []

            root, filename = os.path.split(full_path)
            postprocess_args = postprocess_args.format(
                dir=root,
                filename=filename,
                file=full_path
            )
            process = subprocess.Popen(
                '{} {}'.format(postprocess_cmd, postprocess_args),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True
            )
            out, err = process.communicate()
            utils.logger.debug('Run: {} {}\nstdout: {}\nstderr: {}'.format(
                postprocess_cmd,
                postprocess_args,
                out.decode() if out is not None else '',
                err.decode() if err is not None else '',
            ))

    def recut(self, names=None):
        if settings.RQ_ENABLED:
            self._recut_async(names)
        else:
            self._recut_sync(names)


class UploadedImage(UploadedImageBase, SlaveModelMixin):
    file = models.FileField(_('file'), max_length=255, upload_to=settings.IMAGES_UPLOAD_TO, storage=upload_storage)

    class Meta(UploadedImageBase.Meta):
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def get_variations(self):
        if not hasattr(self, '_variations_cache'):
            owner_field = self.get_owner_field()
            if owner_field is not None:
                self._variations_cache = getattr(owner_field, 'variations')
            else:
                return {}
        return self._variations_cache

    def as_dict(self):
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
