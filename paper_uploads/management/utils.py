from typing import Dict, Type

from django.db import models
from django.db.models.fields import Field

from ..helpers import build_variations
from ..models.base import Resource, VersatileImageResourceMixin
from ..models.collection import CollectionBase, CollectionItemBase
from ..models.fields.collection import CollectionItem
from ..variations import PaperVariation


def is_variations_allowed(model: Type[models.Model]) -> bool:
    """
    Возвращает True, если модель представляет из себя класс изображения с вариациями.
    """
    return issubclass(model, VersatileImageResourceMixin)


def is_collection(model: Type[models.Model]) -> bool:
    """
    Возвращает True, если модель - коллекция.
    """
    return issubclass(model, CollectionBase)


def get_field_variations(field: Field) -> Dict[str, PaperVariation]:
    """
    Получение списка вариаций для поля.
    """
    variation_config = getattr(field, "variations", {}).copy()
    return build_variations(variation_config)


def get_collection_variations(
    collection_cls: Type[CollectionBase], item_type_field: CollectionItem
) -> Dict[str, PaperVariation]:
    """
    Получение списка вариаций для коллекции.
    """
    image_model = item_type_field.model
    variation_config = image_model.get_variation_config(collection_cls, item_type_field)
    return build_variations(variation_config)


def is_resource_field(field: Field):
    """
    Возвращает True, если поле ссылается на Resource (но не на элемент коллекции).
    """
    return (
        field.is_relation
        and field.concrete
        and not field.auto_created
        and issubclass(field.related_model, Resource)
        and not issubclass(field.related_model, CollectionItemBase)
    )


def includes_variations(model: Type[models.Model]) -> bool:
    """
    Проверка наличия вариаций в рамках модели.

    Если модель - коллекция, проверяется наличие хотя бы одного класса элементов,
    поддерживающего вариации изображений.
    Если модель - обыкновенная, проверяется наличие поля ImageField (или аналогичного),
    которое ссылается на ресурс, поддерживающий вариативность изображений.
    """
    if is_collection(model):
        return any(
            is_variations_allowed(field.model)
            for field in model.item_types.values()
        )
    else:
        return any(
            is_resource_field(field) and is_variations_allowed(field.related_model)
            for field in model._meta.get_fields(include_hidden=True)
        )
