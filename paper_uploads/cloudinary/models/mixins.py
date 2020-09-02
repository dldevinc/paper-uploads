import os
import tempfile

import requests
from django.core.files import File
from filelock import FileLock

from ... import utils
from ...conf import settings


class ReadonlyCloudinaryFileProxyMixin:
    """
    Проксирование некоторых свойств файла (только для чтения) на уровень модели
    """

    _wrapped_file = None

    seek = property(lambda self: self._wrapped_file.seek)
    tell = property(lambda self: self._wrapped_file.tell)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    @property
    def closed(self):
        file = self._wrapped_file
        return not file or file.closed

    def open(self, mode='rb'):
        self._require_file()  # noqa
        self.download_file(mode)
        return self
    open.alters_data = True

    def read(self, size=None):
        self._require_file()  # noqa
        return self._wrapped_file.read(size)  # noqa

    def close(self):
        if self._wrapped_file is not None:
            self._wrapped_file.close()
            self._wrapped_file = None

    def readable(self):
        if self.closed:
            return False
        if hasattr(self._wrapped_file, 'readable'):
            return self._wrapped_file.readable()
        return True

    def writable(self):
        if self.closed:
            return False
        if hasattr(self._wrapped_file, 'writable'):
            return self._wrapped_file.writable()
        return 'w' in getattr(self._wrapped_file, 'mode', '')

    def seekable(self):
        if self.closed:
            return False
        if hasattr(self._wrapped_file, 'seekable'):
            return self._wrapped_file.seekable()
        return True

    @property
    def url(self):
        self._require_file()  # noqa
        return self.get_file().url  # noqa

    def download_file(self, mode='rb'):
        if self._wrapped_file is None:
            self._wrapped_file = self._download_file(mode)
        self._wrapped_file.seek(0)

    def _download_file(self, mode='rb') -> File:
        temp_filepath = os.path.join(
            tempfile.gettempdir(),
            settings.CLOUDINARY_TEMP_DIR,
            self.get_file().name  # noqa
        )
        root, basename = os.path.split(temp_filepath)
        os.makedirs(root, mode=0o755, exist_ok=True)

        if os.path.exists(temp_filepath):
            with open(temp_filepath, 'rb') as fp:
                file_checksum = utils.checksum(fp)
            if file_checksum == self.content_hash:  # noqa
                return File(open(temp_filepath, mode))

        lock = FileLock(temp_filepath + '.lock')
        with lock.acquire(timeout=3600):
            response = requests.get(self.get_file_url(), stream=True)  # noqa
            response.raise_for_status()

            with open(temp_filepath, 'wb+') as fp:
                for chunk in response.iter_content():
                    fp.write(chunk)
            return File(open(temp_filepath, mode))
