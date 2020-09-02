import tempfile
from typing import IO

import requests


class ReadonlyCloudinaryFileProxyMixin:
    """
    Проксирование некоторых свойств файла (только для чтения) на уровень модели
    """

    _wrapped_file = None
    SPOOL_SIZE = 10 * 1024 * 1024

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
        # TODO: хранить скачанный файл, проверять checksum вместо повторного скачивания
        # TODO: lock
        # TODO: swap mode to non-writable after download
        if self._wrapped_file is None:
            self._wrapped_file = self._download_file(mode)
        self._wrapped_file.seek(0)

    def _download_file(self, mode='rb') -> IO:
        response = requests.get(self.get_file_url(), stream=True)  # noqa
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
