import datetime
import posixpath
from typing import Optional

import cloudinary.exceptions
import requests
from cloudinary import CloudinaryResource, uploader
from cloudinary.utils import upload_params
from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils.functional import cached_property

from ...conf import settings
from ...logging import logger
from ...models.base import FileResource


class CloudinaryFieldFile:
    """
    Реализация интерфейса django.core.files.File для Cloudinary
    """
    DEFAULT_CHUNK_SIZE = 64 * 2 ** 10

    fileno = property(lambda self: self._response.raw.fileno)
    flush = property(lambda self: self._response.raw.flush)
    isatty = property(lambda self: self._response.raw.isatty)
    readinto = property(lambda self: self._response.raw.readinto)
    readline = property(lambda self: self._response.raw.readline)
    readlines = property(lambda self: self._response.raw.readlines)
    seek = property(lambda self: self._response.raw.seek)
    tell = property(lambda self: self._response.raw.tell)
    truncate = property(lambda self: self._response.raw.truncate)
    writelines = property(lambda self: self._response.raw.writelines)

    def __init__(self, resource: CloudinaryResource, name=None, type=None, resource_type=None):
        self.resource = resource
        if name is None:
            name = resource.public_id
        self.name = name
        self.type = type or resource.type
        self.resource_type = resource_type or resource.resource_type
        self.mode = None
        self._response = None

    def __str__(self):
        return self.name or ''

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self or "None")

    def __bool__(self):
        return bool(self.name)

    def __len__(self):
        return self.size

    def __eq__(self, other):
        return self.url == other.url

    @cached_property
    def metadata(self):
        if self.resource.metadata is not None:
            return self.resource.metadata
        data = uploader.explicit(
            self.resource.public_id,
            type=self.type,
            resource_type=self.resource_type
        )
        return data

    @property
    def size(self) -> int:
        return self.metadata['bytes']

    @property
    def url(self) -> str:
        return self.metadata['secure_url']

    @property
    def format(self) -> Optional[str]:
        return self.metadata.get('format')

    def get_response(self, **kwargs):
        response = requests.get(self.url, **kwargs)
        response.raise_for_status()
        return response

    def chunks(self, chunk_size=None):
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        response = self.get_response(stream=True)
        decode_unicode = self.mode and 'b' not in self.mode
        for chunk in response.iter_content(chunk_size=chunk_size, decode_unicode=decode_unicode):
            yield chunk

    def multiple_chunks(self, chunk_size=None):
        return self.size > (chunk_size or self.DEFAULT_CHUNK_SIZE)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def open(self, mode=None):
        self._response = self.get_response(stream=True)
        self.mode = mode or 'rb'
        return self

    def close(self):
        self._response.close()
        self._response = None
        self.mode = None

    @property
    def closed(self):
        return self._response is None

    def readable(self):
        return True

    def writable(self):
        return False

    def seekable(self):
        return False

    def read(self, size=None):
        data = self._response.raw.read(size)
        decode_unicode = self.mode and 'b' not in self.mode
        if decode_unicode:
            data = data.decode()
        return data


class CloudinaryFileResource(FileResource):
    class Meta(FileResource.Meta):
        abstract = True

    def get_file(self) -> CloudinaryFieldFile:
        raise NotImplementedError

    def get_file_name(self) -> str:
        self._require_file()
        return self.get_file().name

    def get_file_size(self) -> int:
        self._require_file()
        return self.get_file().size

    def get_file_url(self) -> str:
        self._require_file()
        return self.get_file().url

    def file_exists(self) -> bool:
        file = self.get_file()
        if not file:
            return False

        try:
            uploader.explicit(
                self.get_file_name(),
                type=file.type,
                resource_type=file.resource_type,
            )
        except cloudinary.exceptions.Error:
            return False
        return True

    def get_cloudinary_options(self):
        global_options = settings.CLOUDINARY or {}
        options = global_options.get('uploader', {}).copy()

        file_field = self.get_file_field()
        options.update(file_field.options)

        # owner field`s options should override `CloudinaryField` options
        owner_field = self.get_owner_field()
        if owner_field is not None and hasattr(owner_field, 'cloudinary'):
            options.update(owner_field.cloudinary or {})

        # filter keys
        options = {
            key: value
            for key, value in options.items()
            if key in upload_params + uploader.upload_options
        }

        # format folder
        folder = options.pop('folder', None)
        if folder is not None:
            options['folder'] = datetime.datetime.now().strftime(folder)

        return options

    def _attach_file(self, file: File, **options):
        cloudinary_options = self.get_cloudinary_options()
        cloudinary_options.update(options.get('cloudinary', {}))

        if file.size >= 100 * 1024 * 1024:
            upload = uploader.upload_large
        else:
            upload = uploader.upload

        file_field = self.get_file_field()

        try:
            result = upload(
                file,
                type=file_field.type,
                resource_type=file_field.resource_type,
                **cloudinary_options,
            )
        except cloudinary.exceptions.Error as e:
            raise ValidationError(*e.args)

        resource = CloudinaryResource(
            result["public_id"],
            version=str(result["version"]),
            format=result.get("format"),
            type=result["type"],
            resource_type=result["resource_type"],
            metadata=result,
        )

        self.set_file(resource)
        return result

    def _rename_file(self, new_name: str, **options):
        # TODO: Cloudinary can't copy files. We dont't want to do it manually
        file = self.get_file()

        old_name = self.get_file_name()
        folder, basename = posixpath.split(old_name)
        if file.resource_type != 'raw':
            # video and image have no extension
            base, ext = posixpath.splitext(new_name)
            new_name = base
        new_name = posixpath.join(folder, new_name)

        try:
            result = uploader.rename(
                old_name,
                new_name,
                type=file.type,
                resource_type=file.resource_type,
            )
        except cloudinary.exceptions.Error:
            logger.exception(
                "Couldn't rename Cloudinary file: {}".format(self.get_file_name())
            )
            return

        resource = CloudinaryResource(
            result["public_id"],
            version=str(result["version"]),
            format=result.get("format"),
            type=result["type"],
            resource_type=result["resource_type"],
            metadata=result,
        )
        self.set_file(resource)

    def _delete_file(self):
        file = self.get_file()

        try:
            result = uploader.destroy(
                self.get_file_name(),
                type=file.type,
                resource_type=file.resource_type,
            )
        except cloudinary.exceptions.Error:
            logger.exception(
                "Couldn't delete Cloudinary file: {}".format(self.get_file_name())
            )
            return

        status = result.get('result')
        if status == 'ok':
            self.set_file(None)
        else:
            logger.warning(
                "Unable to delete Cloudinary file `{}`: {}".format(
                    self.get_file_name(), status
                )
            )
