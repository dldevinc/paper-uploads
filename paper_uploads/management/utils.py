from typing import Dict, Type

from django.db import models
from django.db.models.fields import Field

from ..helpers import build_variations
from ..models.base import VersatileImageResourceMixin
from ..models.collection import CollectionBase
from ..models.fields.collection import CollectionItem
from ..variations import PaperVariation


def get_model_name(model: Type[models.Model]) -> str:
    return "{}.{}".format(
        model._meta.app_label,
        model.__name__
    )


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
