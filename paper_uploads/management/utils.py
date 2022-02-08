from typing import List, Type

from django.db import models
from django.db.models.fields import Field

from ..helpers import build_variations
from ..models.base import VersatileImageResourceMixin
from ..models.collection import CollectionBase
from ..models.fields.collection import CollectionItem


def is_variations_allowed(model: Type[models.Model]) -> bool:
    """
    Возвращает True, если модель представляет из себя класс изображения с вариациями.
    """
    return issubclass(model, VersatileImageResourceMixin)


def is_collection(model: Type[models.Model]) -> bool:
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
