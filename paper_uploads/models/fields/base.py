from typing import Dict, Any
from django.db import models
from django.core import checks
from django.db.models.signals import post_delete
from ... import validators


class FileFieldBase(models.OneToOneField):
    def __init__(self, verbose_name=None, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('related_name', '+')
        kwargs.setdefault('on_delete', models.SET_NULL)
        kwargs['verbose_name'] = verbose_name
        super().__init__(**kwargs)

    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_relation_class()
        ]

    def _check_relation_class(self):
        from ...models.base import UploadedFileBase, SlaveModelMixin

        rel_is_string = isinstance(self.remote_field.model, str)
        if rel_is_string:
            return []

        model_name = self.remote_field.model if rel_is_string else self.remote_field.model._meta.object_name
        if (not issubclass(self.remote_field.model, UploadedFileBase)
                or not issubclass(self.remote_field.model, SlaveModelMixin)):
            return [
                checks.Error(
                    "Field defines a relation with model '%s', which is not "
                    "subclass of both UploadedFileBase and SlaveModelMixin" % model_name,
                    obj=self,
                )
            ]
        return []

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'null' in kwargs and self.null:
            del kwargs['null']
        if 'related_name' in kwargs and kwargs['related_name'] == '+':
            del kwargs['related_name']
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        return super().formfield(**{
            'owner_app_label': self.opts.app_label.lower(),
            'owner_model_name': self.opts.model_name.lower(),
            'owner_fieldname': self.name,
            'validation': self.get_validation(),
            **kwargs
        })

    def contribute_to_class(self, cls, *args, **kwargs):
        super().contribute_to_class(cls, *args, **kwargs)
        if not cls._meta.abstract:
            post_delete.connect(self.post_delete_callback, sender=cls)

    def post_delete_callback(self, **kwargs):
        """
        Удаление модели файла при удалении владельца
        """
        uploaded = getattr(kwargs['instance'], self.name)
        if uploaded:
            uploaded.delete()

    def run_validators(self, value):
        """
        Отключение валидаторов для файловых полей, т.к. нам нужно валидировать
        не ID OneToOneField, а загружаемые файлы.
        """
        return

    def get_validation(self) -> Dict[str, Any]:
        """
        Возвращает конфигурацию валидации загружаемых файлов FineUploader.
        см. https://docs.fineuploader.com/branch/master/api/options.html#validation

        image.minWidth и т.п. не используются из-за недостатка кастомизации
        текста о ошибках.
        """
        validation = {}
        for v in self.validators:
            if isinstance(v, validators.ExtensionValidator):
                validation['allowedExtensions'] = v.allowed
            elif isinstance(v, validators.MimetypeValidator):
                validation['acceptFiles'] = v.allowed
            elif isinstance(v, validators.SizeValidator):
                validation['sizeLimit'] = v.limit_value
            elif isinstance(v, validators.ImageMinSizeValidator):
                validation['minImageWidth'] = v.width_limit
                validation['minImageHeight'] = v.height_limit
            elif isinstance(v, validators.ImageMaxSizeValidator):
                validation['maxImageWidth'] = v.width_limit
                validation['maxImageHeight'] = v.height_limit
        return validation