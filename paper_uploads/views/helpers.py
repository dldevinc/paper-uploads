from typing import Type, TypeVar

from django.contrib.contenttypes.models import ContentType
from django.db import models

from .. import exceptions

T = TypeVar('T')


def get_model_class(content_type_id: int, base_class: Type[T]) -> Type[T]:
    """
    Получение класса модели загружаемого файла по ContentType ID.
    """
    try:
        content_type = ContentType.objects.get(pk=content_type_id)
    except ContentType.DoesNotExist:
        raise exceptions.InvalidContentType(content_type_id)

    model_class = content_type.model_class()
    if issubclass(model_class, base_class):
        return model_class

    raise exceptions.InvalidContentType(content_type_id)


def get_instance(model_class: Type[models.Model], instance_id: int) -> models.Model:
    """
    Получение экземпляра модели загружаемого файла.
    """
    try:
        instance_id = int(instance_id)
    except (ValueError, TypeError):
        raise exceptions.InvalidObjectId(instance_id)
    else:
        return model_class._default_manager.get(pk=instance_id)  # noqa
