import datetime
import os
import pathlib
import posixpath
from typing import Any, Dict

from django.core import checks
from django.core.exceptions import SuspiciousFileOperation
from django.db import models
from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_delete

try:
    from django.core.files.utils import validate_file_name
except ImportError:
    # new in Django 3.1.10
    def validate_file_name(name, allow_relative_path=False):
        if os.path.basename(name) in {'', '.', '..'}:
            raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)

        if allow_relative_path:
            # Use PurePosixPath() because this branch is checked only in
            # FileField.generate_filename() where all file paths are expected to be
            # Unix style (with forward slashes).
            path = pathlib.PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts:
                raise SuspiciousFileOperation(
                    "Detected path traversal attempt in '%s'" % name
                )
        elif name != os.path.basename(name):
            raise SuspiciousFileOperation("File name '%s' includes path elements" % name)
        return name

from ... import validators


class ResourceFieldBase(models.OneToOneField):
    """
    Базовый класс для ссылок на ресурсы.
    """

    def __init__(self, verbose_name=None, **kwargs):
        kwargs.setdefault("null", True)
        kwargs.setdefault("related_name", "+")
        kwargs.setdefault("on_delete", models.SET_NULL)
        kwargs["verbose_name"] = verbose_name
        super().__init__(**kwargs)

    def check(self, **kwargs):
        return [*super().check(**kwargs), *self._check_relation()]

    def _check_relation(self):
        from ...models.base import Resource

        return self._check_relation_class(
            Resource,
            "Field defines a relation with model '%s', "
            "which is not subclass of Resource model",
        )

    def _check_relation_class(self, base, error_message):
        rel_is_string = isinstance(self.remote_field.model, str)
        if rel_is_string:
            return []

        model_name = (
            self.remote_field.model
            if rel_is_string
            else self.remote_field.model._meta.object_name
        )

        if not issubclass(self.remote_field.model, base):
            return [checks.Error(error_message % model_name, obj=self)]
        return []

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if "null" in kwargs and self.null:
            del kwargs["null"]
        if "related_name" in kwargs and kwargs["related_name"] == "+":
            del kwargs["related_name"]
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "owner_app_label": self.opts.app_label.lower(),
                "owner_model_name": self.opts.model_name.lower(),
                "owner_fieldname": self.name,
                **kwargs,
            }
        )

    def run_validators(self, value):
        """
        Валидаторы мы хотим запускать по отношению в экземпляру File,
        а не к ID экземпляа модели.
        """
        pass

    def contribute_to_class(self, cls, *args, **kwargs):
        super().contribute_to_class(cls, *args, **kwargs)
        if not cls._meta.abstract:
            post_delete.connect(self.post_delete_callback, sender=cls)

    def post_delete_callback(self, **kwargs):
        """
        При удалении модели-владельца поля, удаляем и связанный
        в ним экземпляр ресурса.
        """
        owner_instance = kwargs["instance"]
        resource_id = getattr(owner_instance, self.attname)
        if resource_id:
            # Удаление через `owner_instance.file.delete()` приведёт к зацикленности
            # в случае использования `on_delete=CASCADE`. Поэтому используем фильтрацию
            # по pk.
            self.related_model._base_manager.filter(pk=resource_id).delete()


class FileResourceFieldBase(ResourceFieldBase):
    """
    Базовый класс для полей, которые загружают файлы.
    """
    def __init__(self, *args, upload_to="", storage=None, **kwargs):
        self.storage = storage
        self.upload_to = upload_to
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["storage"] = self.storage
        kwargs["upload_to"] = self.upload_to
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        return super().formfield(**{"configuration": self.get_configuration(), **kwargs})

    def get_configuration(self) -> Dict[str, Any]:
        """
        Превращает Django-валидаторы в словарь конфигурации,
        который может использоваться для вывода или проверки
        на стороне клиента.
        """
        config = {}
        for v in self.validators:
            if isinstance(v, validators.MimeTypeValidator):
                config["acceptFiles"] = v.allowed
            elif isinstance(v, validators.ExtensionValidator):
                config["allowedExtensions"] = v.allowed
            elif isinstance(v, validators.MaxSizeValidator):
                config["sizeLimit"] = v.limit_value
            elif isinstance(v, validators.ImageMinSizeValidator):
                config["minImageWidth"] = v.width_limit
                config["minImageHeight"] = v.height_limit
            elif isinstance(v, validators.ImageMaxSizeValidator):
                config["maxImageWidth"] = v.width_limit
                config["maxImageHeight"] = v.height_limit
        return config


class DynamicStorageFieldFile(FieldFile):
    def __init__(self, instance, field, name):
        super(FieldFile, self).__init__(None, name)
        self.instance = instance
        self.field = field
        self.storage = instance.get_file_storage()
        self._committed = True

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.storage = self.instance.get_file_storage()


class DynamicStorageFileField(models.FileField):
    """
    FileField, который получает значения `storage` и `upload_to`, вызывая методы
    `get_file_storage()` и `get_file_folder()` экземпляра соответственно.
    """
    attr_class = DynamicStorageFieldFile

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, **kwargs):
        self._primary_key_set_explicitly = "primary_key" in kwargs
        kwargs.setdefault("max_length", 255)
        super(models.FileField, self).__init__(verbose_name, name, **kwargs)

    def check(self, **kwargs):
        return [
            *super(models.FileField, self).check(**kwargs),
            *self._check_primary_key(),
        ]

    def deconstruct(self):
        name, path, args, kwargs = super(models.FileField, self).deconstruct()
        if kwargs.get("max_length") == 255:
            del kwargs["max_length"]
        return name, path, args, kwargs

    def generate_filename(self, instance, filename):
        storage = instance.get_file_storage()
        upload_to = instance.get_file_folder()

        dirname = datetime.datetime.now().strftime(upload_to)
        filename = posixpath.join(dirname, filename)
        filename = validate_file_name(filename, allow_relative_path=True)
        return storage.generate_filename(filename)
