import datetime
import os
import posixpath
import tempfile
from io import UnsupportedOperation
from typing import Optional

import cloudinary.exceptions
import requests
from cloudinary import CloudinaryResource, uploader
from cloudinary.utils import upload_params
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.utils import FileProxyMixin
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from filelock import FileLock

from ... import exceptions, helpers, utils
from ...conf import settings
from ...logging import logger
from ...models.base import FileResource
from .mixins import ReadonlyCloudinaryFileProxyMixin


class CloudinaryFieldFile(FileProxyMixin):
    """
    Реализация интерфейса django.core.files.File для Cloudinary
    """
    DEFAULT_CHUNK_SIZE = 64 * 2 ** 10

    def __init__(self, resource: CloudinaryResource, checksum: str = None):
        self.resource = resource
        self.name = self.public_id
        self.checksum = checksum
        self.file = None

    def __str__(self):
        return self.name or ""

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self or "None")

    def __bool__(self):
        return bool(self.name)

    def __len__(self):
        return self.size

    def __eq__(self, other):
        return self.url == other.url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    @cached_property
    def public_id(self):
        public_id = self.resource.public_id
        if (self.resource.resource_type == "raw") and self.resource.format:
            public_id += "." + self.resource.format
        return public_id

    @cached_property
    def metadata(self):
        if self.resource.metadata is not None:
            return self.resource.metadata

        return uploader.explicit(
            self.public_id,
            type=self.resource.type,
            resource_type=self.resource.resource_type
        )

    @property
    def url(self) -> str:
        return self.resource.url

    @property
    def size(self) -> int:
        return self.metadata["bytes"]

    @property
    def format(self) -> Optional[str]:
        return self.metadata.get("format")

    def _get_tempfile_path(self):
        return os.path.join(
            tempfile.gettempdir(),
            settings.CLOUDINARY_TEMP_DIR,
            self.name
        )

    def _download_file(self, mode="rb", chunk_size=None):
        """
        Скачивание файла из Cloudinary во временную директорию.
        Загруженный файл остается там даже после закрытия, чтобы не
        скачивать его заново в следующий раз.
        """
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        tempfile_path = self._get_tempfile_path()
        if os.path.exists(tempfile_path):
            with open(tempfile_path, "rb") as fp:
                file_checksum = utils.checksum(fp)
            if file_checksum == self.checksum:
                return File(open(tempfile_path, mode))

        root, basename = os.path.split(tempfile_path)
        os.makedirs(root, mode=0o755, exist_ok=True)

        lock = FileLock(tempfile_path + ".lock")
        with lock.acquire(timeout=3600):
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            with open(tempfile_path, "wb+") as fp:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    fp.write(chunk)
            return File(open(tempfile_path, mode))

    def open(self, mode="rb"):
        if self.file is None:
            self.file = self._download_file(mode)
        elif self.file.closed:
            self.file.open(mode)
        else:
            self.seek(0)
        return self

    def read(self, size=None):
        if not self.closed:
            return self.file.read(size)
        raise ValueError("Cannot read from file.")

    def write(self, chunk):
        if not self.closed:
            return self.file.write(chunk)
        raise ValueError("Cannot write to file.")

    def close(self):
        self.file.close()

    def multiple_chunks(self, chunk_size=None):
        return self.size > (chunk_size or self.DEFAULT_CHUNK_SIZE)

    def chunks(self, chunk_size=None):
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        try:
            self.seek(0)
        except (AttributeError, UnsupportedOperation):
            pass

        while True:
            data = self.read(chunk_size)
            if not data:
                break
            yield data


class CloudinaryFileResource(ReadonlyCloudinaryFileProxyMixin, FileResource):
    class Meta(FileResource.Meta):
        abstract = True

    @property
    def name(self) -> str:
        self._require_file()
        return self.get_file().name

    def get_file_folder(self) -> str:
        """
        Возвращает путь к папке, в которую будет сохранен файл.
        Результат вызова используется в параметре `folder` для Cloudinary.
        """
        return ""

    def get_file(self) -> CloudinaryFieldFile:
        raise NotImplementedError

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

        file_field = self.get_file_field()

        try:
            uploader.explicit(
                self.name,
                type=file_field.type,
                resource_type=file_field.resource_type,
            )
        except cloudinary.exceptions.Error:
            return False
        return True

    def get_cloudinary_options(self):
        options = (settings.CLOUDINARY_UPLOADER_OPTIONS or {}).copy()

        file_field = self.get_file_field()
        options.update(file_field.options)

        # owner field`s options should override `CloudinaryField` options
        owner_field = self.get_owner_field()
        if owner_field is not None and hasattr(owner_field, "cloudinary"):
            options.update(owner_field.cloudinary or {})

        # filter keys
        options = {
            key: value
            for key, value in options.items()
            if key in upload_params + uploader.upload_options
        }

        # format folder
        folder = options.pop("folder", None)
        if folder is None:
            folder = self.get_file_folder()
        if isinstance(folder, str):
            options["folder"] = datetime.datetime.now().strftime(folder)

        return options

    def _attach_file(self, file: File, **options):
        cloudinary_options = self.get_cloudinary_options()
        cloudinary_options.update(options.get("cloudinary", {}))

        if file.size >= 100 * 1024 * 1024:
            upload = uploader.upload_large
        else:
            upload = uploader.upload

        file_field = self.get_file_field()
        cloudinary_options.setdefault("type", file_field.type)
        cloudinary_options.setdefault("resource_type", file_field.resource_type)

        try:
            result = upload(
                file,
                **cloudinary_options,
            )
        except cloudinary.exceptions.Error as e:
            if e.args and "Unsupported file type" in e.args[0]:
                raise exceptions.UnsupportedFileError(
                    _("File `%s` is not an image") % file.name
                )
            else:
                raise ValidationError(*e.args)

        # fix difference between `public_id` in response
        # and `public_id` in CloudinaryField
        file_format = result.get("format")
        if file_format:
            public_id = result["public_id"]
        else:
            public_id, file_format = posixpath.splitext(result["public_id"])
            file_format = file_format.lstrip(".")

        resource = CloudinaryResource(
            public_id,
            version=str(result["version"]),
            format=file_format,
            type=result["type"],
            resource_type=result["resource_type"],
            metadata=result,
        )

        self.set_file(resource)

        self.basename = helpers.get_filename(file.name)
        self.extension = file_format or ""
        return result

    def _rename_file(self, new_name: str, **options):
        # TODO: Cloudinary can't copy files. We dont't want to do it manually
        cloudinary_options = self.get_cloudinary_options()
        cloudinary_options.update(options.get("cloudinary", {}))

        file_field = self.get_file_field()
        cloudinary_options.setdefault("type", file_field.type)
        cloudinary_options.setdefault("resource_type", file_field.resource_type)

        old_name = self.name
        folder, basename = posixpath.split(old_name)
        if cloudinary_options["resource_type"] != "raw":
            # video and image have no extension
            base, ext = posixpath.splitext(new_name)
            new_name = base
        new_name = posixpath.join(folder, new_name)

        try:
            result = uploader.rename(
                old_name,
                new_name,
                **cloudinary_options
            )
        except cloudinary.exceptions.Error as e:
            raise ValidationError(*e.args)

        # fix difference between `public_id` in response
        # and `public_id` in CloudinaryField
        file_format = result.get("format")
        if file_format:
            public_id = result["public_id"]
        else:
            public_id, file_format = posixpath.splitext(result["public_id"])
            file_format = file_format.lstrip(".")

        resource = CloudinaryResource(
            public_id,
            version=str(result["version"]),
            format=file_format,
            type=result["type"],
            resource_type=result["resource_type"],
            metadata=result,
        )
        self.set_file(resource)

        self.basename = helpers.get_filename(new_name)
        self.extension = file_format or ""
        return result

    def _delete_file(self, **options):
        cloudinary_options = self.get_cloudinary_options()
        cloudinary_options.update(options.get("cloudinary", {}))

        file = self.get_file()
        if not file:
            return

        file_field = self.get_file_field()
        cloudinary_options.setdefault("type", file_field.type)
        cloudinary_options.setdefault("resource_type", file_field.resource_type)

        try:
            result = uploader.destroy(
                self.name,
                **cloudinary_options
            )
        except cloudinary.exceptions.Error:
            logger.exception(
                "Couldn't delete Cloudinary file: {}".format(self.name)
            )
            return

        status = result.get("result")
        if status == "ok":
            self.set_file(None)
        else:
            logger.warning(
                "Unable to delete Cloudinary file `{}`: {}".format(
                    self.name, status
                )
            )
        return result

    def build_url(self, **options):
        # proxy Cloudinary method
        self._require_file()
        file = self.get_file()
        return file.resource.build_url(**options)
