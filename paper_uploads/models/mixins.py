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

        try:
            return owner_model._meta.get_field(self.owner_fieldname)
        except FieldDoesNotExist:
            logger.debug(
                "Not found field '%s' in model %s.%s"
                % (self.owner_app_label, self.owner_model_name, self.owner_fieldname)
            )


class FileProxyMixin:
    """
    Проксирование некоторых свойств файла на уровень модели
    """

    seek = property(lambda self: self.get_file().seek)
    tell = property(lambda self: self.get_file().tell)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    @property
    def closed(self):
        file = self.get_file()  # noqa
        return not file or file.closed

    def open(self, mode='rb'):
        self._require_file()  # noqa
        return self.get_file().open(mode)  # noqa
    open.alters_data = True  # noqa

    def read(self, size=None):
        self._require_file()  # noqa
        return self.get_file().read(size)  # noqa

    def close(self):
        self.get_file().close()  # noqa


class FileFieldProxyMixin:
    """
    Проксирование некоторых свойств файла (только для чтения) на уровень модели
    """

    @property
    def path(self):
        self._require_file()  # noqa
        return self.get_file().path

    @property
    def url(self):
        self._require_file()  # noqa
        return self.get_file().url
