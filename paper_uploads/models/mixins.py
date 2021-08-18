from typing import Optional, Type

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models

from ..logging import logger


class BacklinkModelMixin(models.Model):
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
            return None

        try:
            return apps.get_model(self.owner_app_label, self.owner_model_name)
        except LookupError:
            logger.debug(
                "Not found model: %s.%s" % (self.owner_app_label, self.owner_model_name)
            )

    def get_owner_field(self) -> Optional[models.Field]:
        owner_model = self.get_owner_model()
        if owner_model is None:
            return None

        if not self.owner_fieldname:
            return None

        try:
            return owner_model._meta.get_field(self.owner_fieldname)
        except FieldDoesNotExist:
            logger.debug(
                "Not found field '%s' in model %s.%s"
                % (self.owner_app_label, self.owner_model_name, self.owner_fieldname)
            )


class FileProxyMixin:
    """
    Проксирование некоторых свойств файла на уровень модели.

    Открытый файл сохраняется в поле `__file`, чтобы предотвратить
    повторное скачивание файла при повторном открытии файла.
    """

    def __init__(self, *args, **kwargs):
        self.__file = None
        super().__init__(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def _get_file(self):
        return getattr(self, "_FileProxyMixin__file", None)

    def _open_file(self, mode):
        self.__file = self.get_file().open(mode)  # noqa: F821

    def _close_file(self):
        file = self._get_file()
        if file is not None:
            file.close()
        self.__file = None

    @property
    def closed(self):
        file = self._get_file()
        if file is None:
            file = self.get_file()  # noqa: F821
        return not file or file.closed

    def open(self, mode="rb"):
        self._require_file()  # noqa: F821

        file = self._get_file()
        if file is None:
            self._open_file(mode)
        elif file.seekable():
            file.seek(0)
        else:
            # current file is not seekable - reopen it
            file.close()
            self._open_file(mode)
        return self
    open.alters_data = True  # noqa: F821

    def read(self, size=None):
        self._require_file()  # noqa: F821

        file = self._get_file()
        if file is None:
            file = self.get_file()  # noqa: F821

        return file.read(size)  # noqa: F821

    def close(self):
        self._close_file()

    def readable(self):
        file = self._get_file()
        if file is None:
            file = self.get_file()  # noqa: F821
        if hasattr(file, "readable"):
            return file.readable()
        return True

    def writable(self):
        file = self._get_file()
        if file is None:
            file = self.get_file()  # noqa: F821
        if hasattr(file, "writable"):
            return file.writable()
        return "w" in getattr(file, "mode", "")

    def seekable(self):
        file = self._get_file()
        if file is None:
            file = self.get_file()  # noqa: F821
        if hasattr(file, "seekable"):
            return file.seekable()
        return True

    def seek(self, *args, **kwargs):
        file = self._get_file()
        if file is None:
            file = self.get_file()  # noqa: F821
        return file.seek(*args, **kwargs)

    def tell(self):
        file = self._get_file()
        if file is None:
            file = self.get_file()  # noqa: F821
        return file.tell()

    def multiple_chunks(self, chunk_size=None):
        file = self._get_file()
        if file is None:
            file = self.get_file()  # noqa: F821
        return file.multiple_chunks(chunk_size)

    def chunks(self, chunk_size=None):
        file = self._get_file()
        if file is None:
            file = self.get_file()  # noqa: F821
        return file.chunks(chunk_size)


class FileFieldProxyMixin:
    """
    Проксирование некоторых свойств файла (только для чтения) на уровень модели
    """

    @property
    def path(self):
        self._require_file()  # noqa: F821
        return self.get_file().path  # noqa: F821

    @property
    def url(self):
        self._require_file()  # noqa: F821
        return self.get_file().url  # noqa: F821
