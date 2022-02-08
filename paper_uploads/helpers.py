import os
import time
from functools import lru_cache
from typing import Any, Dict, Generator, Iterable, Iterator, List, Set, Tuple, Type

from anytree import Node
from django.apps import apps
from django.core import exceptions
from django.core.exceptions import ObjectDoesNotExist
from django.db import DEFAULT_DB_ALIAS, models

from .conf import settings
from .logging import logger
from .typing import VariationConfig
from .utils import lowercased_dict_keys
from .variations import PaperVariation

# Перечень допустимых версий вариаций
ALLOWED_VERSIONS = {"webp", "2x", "3x", "4x"}

# Максимальное количество попыток чтения из БД при получении
# экземпляра модели. Сделано потому, что каждый запрос оборачивается
# в транзакцию. Из-за этого вызов `recut()` (даже после метода `save()`)
# не гарантирует, что данные уже попали в БД.
# TODO: поискать альтернативные решения
MAX_DB_READ_ATTEMPTS = 3


def get_filename(filename: str) -> str:
    basename = os.path.basename(filename)
    name, _ = os.path.splitext(basename)
    return name


def get_extension(filename: str) -> str:
    basename = os.path.basename(filename)
    _, extension = os.path.splitext(basename)
    return extension.lstrip(".")


def _variation_name(name: str, scale_factor: int = 1, webp: bool = False) -> str:
    if webp:
        variation_name = "{}_webp".format(name)
    else:
        variation_name = name

    if scale_factor == 1:
        pass
    else:
        variation_name = "{}_{}x".format(variation_name, scale_factor)

    return variation_name


def generate_scaled_versions(
    name: str, config: VariationConfig, scale_factor: int = 1, webp: bool = False
) -> Iterator[PaperVariation]:
    """
    Геренирует Retina-версию вариации с опциональной WebP-версией того же размера.
    """
    scaled_size = tuple(x * scale_factor for x in config.get("size", (0, 0)))

    variation_config = dict(
        config,
        name=_variation_name(name, scale_factor),
        size=scaled_size,
        max_width=scale_factor * config.get("max_width", 0),
        max_height=scale_factor * config.get("max_height", 0),
    )

    yield PaperVariation(**variation_config)

    if webp:
        variation_config = dict(
            config,
            name=_variation_name(name, scale_factor, webp=True),
            size=scaled_size,
            max_width=scale_factor * config.get("max_width", 0),
            max_height=scale_factor * config.get("max_height", 0),
            format="webp"
        )

        yield PaperVariation(**variation_config)


def generate_variation_versions(
    name: str, config: VariationConfig, versions: Set[str],
) -> Iterator[PaperVariation]:
    """
    Геренирует все указанные версии вариации по словарю конфигурации
    """
    webp = "webp" in versions and config.get("format", "").upper() != "WEBP"
    yield from generate_scaled_versions(name, config, scale_factor=1, webp=webp)
    if "2x" in versions:
        yield from generate_scaled_versions(name, config, scale_factor=2, webp=webp)
    if "3x" in versions:
        yield from generate_scaled_versions(name, config, scale_factor=3, webp=webp)
    if "4x" in versions:
        yield from generate_scaled_versions(name, config, scale_factor=4, webp=webp)


def build_variations(options: Dict[str, VariationConfig]) -> Dict[str, PaperVariation]:
    """
    Создание объектов вариаций из словаря конфигураций.
    """
    variations = {}
    for name, config in options.items():
        new_config = lowercased_dict_keys(settings.VARIATION_DEFAULTS or {})
        new_config.update(config)

        versions = set(v.lower() for v in new_config.get("versions", ()))
        unknown_versions = versions.difference(ALLOWED_VERSIONS)
        if unknown_versions:
            raise ValueError(
                "unknown variation versions: {}".format(", ".join(unknown_versions))
            )

        variation_name = new_config.get("name", name)

        all_versions = generate_variation_versions(variation_name, new_config, versions)
        for variation in all_versions:
            if variation_name == variation.name:  # определение корневой вариации
                variations[variation_name] = variation
            else:
                variations.setdefault(variation.name, variation)

    return variations


def iterate_variation_names(options: Dict[str, VariationConfig]) -> Iterator[str]:
    """
    Перечисляет имена вариаций из словаря конфигураций с учётом параметра `versions`.
    """
    def iterate_variation_versions(name: str, scale_factor: int = 1, webp: bool = False) -> Iterator[str]:
        yield _variation_name(name, scale_factor)
        if webp:
            yield _variation_name(name, scale_factor, webp=True)

    for name, config in options.items():
        new_config = lowercased_dict_keys(settings.VARIATION_DEFAULTS or {})
        new_config.update(config)

        versions = set(v.lower() for v in config.get("versions", ()))
        webp = "webp" in versions and config.get("format", "").upper() != "WEBP"

        yield from iterate_variation_versions(name, scale_factor=1, webp=webp)
        if "2x" in versions:
            yield from iterate_variation_versions(name, scale_factor=2, webp=webp)
        if "3x" in versions:
            yield from iterate_variation_versions(name, scale_factor=3, webp=webp)
        if "4x" in versions:
            yield from iterate_variation_versions(name, scale_factor=4, webp=webp)


@lru_cache()
def get_resource_model_trees(include_proxy=False) -> Tuple[Node]:
    """
    Возвращает иерархии классов ресурсов в виде anytree.Node.
    """
    from .models.base import Resource

    resource_models = [
        model
        for model in apps.get_models()
        if issubclass(model, Resource) and (include_proxy is True or model._meta.proxy is False)
    ]

    resource_bases = {
        model: [
            base
            for base in model.__mro__[1:]
            if base in resource_models
        ]
        for model in resource_models
    }

    # Иерархии ресурсов, отсортированные по длине
    ordered_resource_bases = sorted(resource_bases.items(), key=lambda p: len(p[1]), reverse=True)

    # Ссылки на все узлы всех деревьев
    node_map = {}

    # Список корневых узлов деревьев
    trees = []  # type: list[Node]

    def _get_or_create_node(model, parent=None):
        if model in node_map:
            return node_map[model]
        else:
            node = Node(model.__name__, model=model, parent=parent)
            node_map[model] = node

            if parent is None:
                trees.append(node)

            return node

    # Перебор цепочек классов от самых длинных к самым коротким гарантирует,
    # что родительские классы появятся в дереве раньше дочерних. Это
    # позволит использовать упрощенный алгоритм построения дерева.
    for model, bases in ordered_resource_bases:
        base_parent = None
        for base in reversed(bases):
            base_parent = _get_or_create_node(base, base_parent)

        _get_or_create_node(model, base_parent)

    return tuple(trees)


@lru_cache()
def get_collection_trees(include_proxy=False) -> Tuple[Node]:
    """
    Возвращает иерархии классов коллекций в виде anytree.Node.
    """
    from .models.collection import Collection

    collection_models = [
        model
        for model in apps.get_models()
        if issubclass(model, Collection) and (include_proxy is True or model._meta.proxy is False)
    ]

    collection_bases = {
        model: [
            base
            for base in model.__mro__[1:]
            if base in collection_models
        ]
        for model in collection_models
    }

    # Иерархии коллекций, отсортированные по длине
    ordered_collection_bases = sorted(collection_bases.items(), key=lambda p: len(p[1]), reverse=True)

    # Ссылки на все узлы всех деревьев
    node_map = {}

    # Список корневых узлов деревьев
    trees = []  # type: list[Node]

    def _get_or_create_node(model, parent=None):
        if model in node_map:
            return node_map[model]
        else:
            node = Node(model.__name__, model=model, parent=parent)
            node_map[model] = node

            if parent is None:
                trees.append(node)

            return node

    # Перебор цепочек классов от самых длинных к самым коротким гарантирует,
    # что родительские классы появятся в дереве раньше дочерних. Это
    # позволит использовать упрощенный алгоритм построения дерева.
    for model, bases in ordered_collection_bases:
        base_parent = None
        for base in reversed(bases):
            base_parent = _get_or_create_node(base, base_parent)

        _get_or_create_node(model, base_parent)

    return tuple(trees)


def get_instance(
    app_label: str, model_name: str, object_id: int, using: str = DEFAULT_DB_ALIAS
):
    """
    Получение экземпляра модели по названию приложения, модели и ID.
    """
    model_class = apps.get_model(app_label, model_name)
    attempts = 1
    while True:
        try:
            return model_class._base_manager.using(using).get(pk=object_id)
        except ObjectDoesNotExist:
            # delay recheck if transaction not committed yet
            attempts += 1
            if attempts > MAX_DB_READ_ATTEMPTS:
                logger.exception("Instance #%s not found" % object_id)
                raise
            else:
                time.sleep(1)


def run_validators(value: Any, validators: Iterable[Any]):
    """
    Based on `django.forms.fields.run_validators` method.
    """
    errors = []  # type: List[Any]
    for v in validators:
        try:
            v(value)
        except exceptions.ValidationError as e:
            errors.extend(e.error_list)

    if errors:
        raise exceptions.ValidationError(errors)


def iterate_parent_models(model: models.Model) -> Generator[Type[models.Model], Any, None]:
    """
    Итерация модели и её родительских классов-моделей.
    """
    for klass in model.__mro__:
        if issubclass(klass, models.Model):
            yield klass


def _get_item_types(cls):
    """
    Получение явно объявленных (не унаследованных) типов элементов коллекции
    из её класса.
    """
    attname = "_{}__item_types".format(cls.__name__)
    return getattr(cls, attname, None)


def _set_item_types(cls, value):
    attname = "_{}__item_types".format(cls.__name__)
    setattr(cls, attname, value)
