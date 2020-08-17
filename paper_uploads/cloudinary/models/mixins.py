import tempfile
from typing import IO

import requests


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
