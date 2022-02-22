from typing import Any, Dict

import django
from django.core import checks
from django.core.files import File
from django.db import models
from django.db.models.fields.files import FieldFile, FileDescriptor
from django.db.models.signals import post_delete

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
        return [
            *super().check(**kwargs),
            *self._check_relation()
        ]

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
            return [
                checks.Error(
                    error_message % model_name,
                    obj=self
                )
            ]
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

    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_upload_to(),
        ]

    def _check_upload_to(self):
        if callable(self.upload_to):
            return [
                checks.Error(
                    "%s's 'upload_to' argument must be a string, not a callable." % self.__class__.__name__,
                    obj=self,
                )
            ]
        elif isinstance(self.upload_to, str) and self.upload_to.startswith('/'):
            return [
                checks.Error(
                    "%s's 'upload_to' argument must be a relative path, not an "
                    "absolute path." % self.__class__.__name__,
                    obj=self,
                    id="fields.E202",
                    hint="Remove the leading slash.",
                )
            ]
        else:
            return []

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

    def __getstate__(self):
        state = super().__getstate__()
        if django.VERSION <= (3, 0):
            state.setdefault("field", self.field)
            state.setdefault("instance", self.instance)

        state.setdefault("storage", self.storage)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Попытка восстановления storage в __setstate__ терпит неудачу из-за
        # того, что в instance ещё нет полей owner_app_label и прочих.


class DynamicStorageFileDescriptor(FileDescriptor):
    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        if django.VERSION <= (3, 1):
            # The instance dict contains whatever was originally assigned
            # in __set__.
            if self.field.name in instance.__dict__:
                file = instance.__dict__[self.field.name]
            else:
                instance.refresh_from_db(fields=[self.field.name])
                file = getattr(instance, self.field.name)

            # If this value is a string (instance.file = "path/to/file") or None
            # then we simply wrap it with the appropriate attribute class according
            # to the file field. [This is FieldFile for FileFields and
            # ImageFieldFile for ImageFields; it's also conceivable that user
            # subclasses might also want to subclass the attribute class]. This
            # object understands how to convert a path to a file, and also how to
            # handle None.
            if isinstance(file, str) or file is None:
                attr = self.field.attr_class(instance, self.field, file)
                instance.__dict__[self.field.name] = attr

            # Other types of files may be assigned as well, but they need to have
            # the FieldFile interface added to them. Thus, we wrap any other type of
            # File inside a FieldFile (well, the field's attr_class, which is
            # usually FieldFile).
            elif isinstance(file, File) and not isinstance(file, FieldFile):
                file_copy = self.field.attr_class(instance, self.field, file.name)
                file_copy.file = file
                file_copy._committed = False
                instance.__dict__[self.field.name] = file_copy

            # Finally, because of the (some would say boneheaded) way pickle works,
            # the underlying FieldFile might not actually itself have an associated
            # file. So we need to reset the details of the FieldFile in those cases.
            elif isinstance(file, FieldFile) and not hasattr(file, "field"):
                file.instance = instance
                file.field = self.field
                file.storage = instance.get_file_storage()

            # Make sure that the instance is correct.
            elif isinstance(file, FieldFile) and instance is not file.instance:
                file.instance = instance

            # That was fun, wasn't it?
            return instance.__dict__[self.field.name]
        else:
            # The instance dict contains whatever was originally assigned
            # in __set__.
            file = super().__get__(instance, cls)

            # If this value is a string (instance.file = "path/to/file") or None
            # then we simply wrap it with the appropriate attribute class according
            # to the file field. [This is FieldFile for FileFields and
            # ImageFieldFile for ImageFields; it's also conceivable that user
            # subclasses might also want to subclass the attribute class]. This
            # object understands how to convert a path to a file, and also how to
            # handle None.
            if isinstance(file, str) or file is None:
                attr = self.field.attr_class(instance, self.field, file)
                instance.__dict__[self.field.attname] = attr

            # Other types of files may be assigned as well, but they need to have
            # the FieldFile interface added to them. Thus, we wrap any other type of
            # File inside a FieldFile (well, the field's attr_class, which is
            # usually FieldFile).
            elif isinstance(file, File) and not isinstance(file, FieldFile):
                file_copy = self.field.attr_class(instance, self.field, file.name)
                file_copy.file = file
                file_copy._committed = False
                instance.__dict__[self.field.attname] = file_copy

            # Finally, because of the (some would say boneheaded) way pickle works,
            # the underlying FieldFile might not actually itself have an associated
            # file. So we need to reset the details of the FieldFile in those cases.
            elif isinstance(file, FieldFile) and not hasattr(file, "field"):
                file.instance = instance
                file.field = self.field
                file.storage = instance.get_file_storage()

            # Make sure that the instance is correct.
            elif isinstance(file, FieldFile) and instance is not file.instance:
                file.instance = instance

            # That was fun, wasn't it?
            return instance.__dict__[self.field.attname]


class DynamicStorageFileField(models.FileField):
    """
    FileField, который проксирует вызов метода `generate_filename()` на модель,
    в которой определено данное поле.
    """
    attr_class = DynamicStorageFieldFile
    descriptor_class = DynamicStorageFileDescriptor

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
        return instance.generate_filename(filename)
