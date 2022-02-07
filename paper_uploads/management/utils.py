from typing import List, Type, Union

from django.db import models
from django.db.models.fields import Field

from ...helpers import build_variations
from ...models.base import VersatileImageResourceMixin
from ...models.collection import CollectionBase
from ...models.fields.collection import CollectionItem


def is_versatile_field(field: Field) -> bool:
    """
    Возвращает True, если поле ссылается на класс изображения с вариациями.
    """
    return field.is_relation and issubclass(
        field.related_model, VersatileImageResourceMixin
    )


def is_versatile_item(field: CollectionItem) -> bool:
    """
    Возвращает True, если поле коллекции подключает класс элемента
    изображения с вариациями.
    """
    return issubclass(field.model, VersatileImageResourceMixin)


def is_collection(model: Type[Union[models.Model, CollectionBase]]) -> bool:
    """
    Возвращает True, если model - коллекция.
    """
    return issubclass(model, CollectionBase)


def get_field_variations(field: Field) -> List[str]:
    """
    Получение списка имен вариаций для поля.
    """
    return list(
        field.variations.keys()
    )


def get_collection_variations(collection_cls: Type[CollectionBase], item_type_field: CollectionItem) -> List[str]:
    """
    Получение списка имен вариаций для коллекции.
    """
    image_model = item_type_field.model
    variation_config = image_model.get_variation_config(collection_cls, item_type_field)
    variations = build_variations(variation_config)
    return list(variations.keys())
