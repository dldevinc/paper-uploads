from typing import Optional, Type

from django.apps import apps
from django.core import checks
from django.core.exceptions import FieldDoesNotExist
from django.core.files import File
from django.db import models
from django.db.models.utils import make_model_tuple
from django.utils.module_loading import import_string

from ..logging import logger


class BacklinkModelMixin(models.Model):
    """
    Миксина, позволяющая обратиться к полю модели, которое ссылается
    на текущий объект.

    Этот миксин должен использоваться в каждой модели, которая используется
    в полях FileField, ImageField или CollectionField.
    """

    owner_app_label = models.CharField(max_length=100, editable=False)
    owner_model_name = models.CharField(max_length=100, editable=False)
    owner_fieldname = models.CharField(max_length=255, editable=False)

    class Meta:
        abstract = True

    def set_owner_field(self, model: Type[models.Model], field_name: str):
        # check field exists
        field = model._meta.get_field(field_name)

        self.owner_app_label, self.owner_model_name = make_model_tuple(model)
        self.owner_fieldname = field.name

    def get_owner_model(self) -> Optional[Type[models.Model]]:
        if not self.owner_app_label or not self.owner_model_name:
            return

        try:
            return apps.get_model(self.owner_app_label, self.owner_model_name)
        except LookupError:
            logger.debug(
                "Not found model: %s.%s" % (self.owner_app_label, self.owner_model_name)
            )

    def get_owner_field(self) -> Optional[models.Field]:
        owner_model = self.get_owner_model()
        if owner_model is None:
            return

        if not self.owner_fieldname:
            return

        try:
            return owner_model._meta.get_field(self.owner_fieldname)
        except FieldDoesNotExist:
            logger.debug(
                "Not found field '%s' in model %s.%s"
                % (self.owner_app_label, self.owner_model_name, self.owner_fieldname)
            )


class FileProxyMixin:
    """
    Миксин, проксирующий некоторые свойства объекта, возвращаемого методом `get_file()`
    на уровень класса, к которому применен миксин.
    """

    def __init__(self, *args, **kwargs):
        self.__file = None
        super().__init__(*args, **kwargs)

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def _require_file(self):
        """
        Требование наличия непустой ссылки на файл.
        Физическое существование файла не гарантируется.
        """
        raise NotImplementedError

    def _get_file(self):
        return self.__file

    def _open_file(self, mode):
        self.__file = self.get_file().open(mode)
        return self.__file

    def get_file(self) -> File:
        raise NotImplementedError

    def open(self, mode="rb"):
        """
        Открытие файла.

        Если файл уже открыт, перемещает курсор в начало файла.
        Если файл не допускает перемещение курсора - файл закрывается и открывается
        заново.
        """
        self._require_file()

        file = self._get_file()
        if file is None:
            return self._open_file(mode)

        if file.seekable() and (not hasattr(file.file, "mode") or file.file.mode == mode):
            file.seek(0)
            return file

        # current file is not seekable - reopen it
        file.close()
        return self._open_file(mode)
    open.alters_data = True

    @property
    def closed(self):
        return self.__file is None or self.__file.closed

    def close(self):
        if self.__file is not None:
            self.__file.close()
            self.__file = None


class FileFieldProxyMixin:
    """
    Проксирование некоторых свойств файла (только для чтения) на уровень модели
    """

    @property
    def path(self):
        return self.get_file().path  # noqa: F821

    @property
    def url(self):
        return self.get_file().url  # noqa: F821


class EditableResourceMixin:
    """
    Добавление поля сос ссылкой на класс формы, через которую
    следует редактировать ресурс в интерфейсе администратора.
    """
    change_form_class: Optional[str] = None

    @classmethod
    def check(cls, **kwargs):
        return [
            *super().check(**kwargs),
            *cls._check_form_class(),
        ]

    @classmethod
    def _check_form_class(cls, **kwargs):
        if cls._meta.abstract or cls.change_form_class is None:
            return []

        errors = []

        try:
            import_string(cls.change_form_class)
        except ImportError:
            errors.append(
                checks.Error(
                    "The value of 'change_form_class' refers to '%s', which does "
                    "not exists" % cls.change_form_class,
                    obj=cls,
                )
            )

        return errors
