import posixpath
import random
import string
import tempfile
from typing import IO

import cloudinary.uploader
import requests
from cloudinary import CloudinaryResource
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils.translation import ugettext_lazy as _

from ...logging import logger
from ...models import FileResource


class CloudinaryFileResource(FileResource):
    cloudinary_resource_type = 'raw'
    cloudinary_type = 'upload'

    file = CloudinaryField(_('file'))

    class Meta(FileResource.Meta):
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cloudinary_field = self._meta.get_field('file')
        cloudinary_field.type = self.cloudinary_type
        cloudinary_field.resource_type = self.cloudinary_resource_type

    def get_file(self) -> CloudinaryResource:
        return self.file or None

    def get_file_name(self) -> str:
        file = self.get_file()
        if file is None:
            return ''

        name = self.get_public_id()
        if file.format and not name.endswith(file.format):
            name += '.{}'.format(file.format)
        return name

    def get_file_url(self) -> str:
        return self.get_file().url

    def is_file_exists(self) -> bool:
        file = self.get_file()
        if file is None:
            return False

        try:
            cloudinary.uploader.explicit(
                self.get_public_id(),
                type=self.cloudinary_type,
                resource_type=self.cloudinary_resource_type,
            )
        except cloudinary.exceptions.Error:
            return False
        return True

    def _attach_file(self, file: File, **options):
        cloudinary_options = options.get('cloudinary', {})

        if file.size >= 100 * 1024 * 1024:
            upload = cloudinary.uploader.upload_large
        else:
            upload = cloudinary.uploader.upload

        try:
            result = upload(
                file,
                type=self.cloudinary_type,
                resource_type=self.cloudinary_resource_type,
                **cloudinary_options,
            )
        except cloudinary.exceptions.Error as e:
            raise ValidationError(*e.args)

        resource = cloudinary.CloudinaryResource(
            result["public_id"],
            version=str(result["version"]),
            format=result.get("format"),
            type=result["type"],
            resource_type=result["resource_type"],
            metadata=result,
        )
        self.file = resource
        return result

    def _rename_file(self, new_name: str):
        old_public_id = self.get_public_id()

        file_dir, file_name = posixpath.split(old_public_id)
        _, format = posixpath.splitext(file_name)
        rand = ''.join(
            random.SystemRandom().choice(string.ascii_lowercase + string.digits)
            for _ in range(6)
        )
        new_name = posixpath.join(file_dir, "{}_{}".format(new_name, rand))
        if self.cloudinary_resource_type == 'raw':
            new_name += format

        try:
            result = cloudinary.uploader.rename(
                old_public_id,
                new_name,
                type=self.cloudinary_type,
                resource_type=self.cloudinary_resource_type,
            )
        except cloudinary.exceptions.Error:
            logger.exception(
                "Couldn't rename Cloudinary file: {}".format(self.get_file_name())
            )
            return
        else:
            resource = cloudinary.CloudinaryResource(
                result["public_id"],
                version=str(result["version"]),
                format=result.get("format"),
                type=result["type"],
                resource_type=result["resource_type"],
                metadata=result,
            )
            self.file = resource

    def _delete_file(self):
        if not self.file:
            return

        try:
            result = cloudinary.uploader.destroy(
                self.get_public_id(),
                type=self.cloudinary_type,
                resource_type=self.cloudinary_resource_type,
            )
        except cloudinary.exceptions.Error:
            logger.exception(
                "Couldn't delete Cloudinary file: {}".format(self.get_file_name())
            )
            return

        status = result.get('result')
        if status == 'ok':
            pass
        else:
            logger.warning(
                "Unable to delete Cloudinary file `{}`: {}".format(
                    self.get_file_name(), status
                )
            )
        self.file = None

    def get_public_id(self) -> str:
        """
        Для картинок и видео public_id не учитывает расширения.
        Для raw - учитывает.
        """
        file = self.get_file()
        if file is None:
            return ''

        if self.cloudinary_resource_type in {'image', 'video'}:
            return file.public_id
        elif self.cloudinary_resource_type == 'raw':
            public_id = file.public_id
            if file.format:
                public_id += '.' + file.format
            return public_id


class ReadonlyCloudinaryFileProxyMixin:
    """
    Проксирование некоторых свойств файла (только для чтения) на уровень модели
    """

    _wrapped_file = None
    SPOOL_SIZE = 10 * 1024 * 1024

    read = property(lambda self: self._wrapped_file.read)
    seek = property(lambda self: self._wrapped_file.seek)
    tell = property(lambda self: self._wrapped_file.tell)
    url = property(lambda self: self.get_file().url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def open(self, mode='rb'):
        self.require_file(mode)
        return self

    open.alters_data = True

    def close(self):
        if self._wrapped_file is not None:
            self._wrapped_file.close()
            self._wrapped_file = None

    @property
    def closed(self):
        if self._wrapped_file is None:
            return True
        return self._wrapped_file.closed

    def require_file(self, mode='rb'):
        if self._wrapped_file is None:
            self._wrapped_file = self._require_file(mode)
        self._wrapped_file.seek(0)

    def _require_file(self, mode='rb') -> IO:
        response = requests.get(self.get_file_url(), stream=True)
        response.raise_for_status()

        bytes_mode = 'b' in mode
        filemode = 'wb+' if bytes_mode else 'w+'
        tfile = tempfile.SpooledTemporaryFile(max_size=self.SPOOL_SIZE, mode=filemode)
        for chunk in response.iter_content():
            if bytes_mode:
                tfile.write(chunk)
            else:
                tfile.write(chunk.decode(response.encoding or 'utf-8'))
        tfile.seek(0)
        return tfile
