from typing import Any, Dict

from django.core import checks
from django.db import models
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
            self.related_model.objects.filter(pk=resource_id).delete()


class FileResourceFieldBase(ResourceFieldBase):
    """
    Базовый класс для полей, которые загружают файлы.
    """

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
            elif isinstance(v, validators.SizeValidator):
                config["sizeLimit"] = v.limit_value
            elif isinstance(v, validators.ImageMinSizeValidator):
                config["minImageWidth"] = v.width_limit
                config["minImageHeight"] = v.height_limit
            elif isinstance(v, validators.ImageMaxSizeValidator):
                config["maxImageWidth"] = v.width_limit
                config["maxImageHeight"] = v.height_limit
        return config
