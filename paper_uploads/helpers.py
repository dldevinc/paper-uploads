import os
import time
from typing import Any, Dict, Iterable, Iterator, List, Set

from django.apps import apps
from django.core import exceptions
from django.core.exceptions import ObjectDoesNotExist
from django.db import DEFAULT_DB_ALIAS

from .conf import settings
from .logging import logger
from .typing import FileLike, VariationConfig
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


def generate_scaled_versions(
    name: str, config: VariationConfig, scale_factor: int = 1, webp: bool = False
) -> Iterator[PaperVariation]:
    """
    Геренирует Retina-версию вариации с опциональной WebP-версией того же размера.
    """
    scaled_size = tuple(x * scale_factor for x in config.get("size", (0, 0)))

    if scale_factor == 1:
        variation_name = name
    else:
        variation_name = "{}_{}x".format(name, scale_factor)

    variation_config = dict(
        config,
        name=variation_name,
        size=scaled_size,
        max_width=scale_factor * config.get("max_width", 0),
        max_height=scale_factor * config.get("max_height", 0),
    )

    yield PaperVariation(**variation_config)

    if webp:
        if scale_factor == 1:
            variation_name = "{}_webp".format(name)
        else:
            variation_name = "{}_webp_{}x".format(name, scale_factor)

        variation_config = dict(
            config,
            name=variation_name,
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

        all_versions = generate_variation_versions(name, new_config, versions)
        for variation in all_versions:
            if name == variation.name:
                # явно заданная вариация переопредеяет любую неявную
                variations[name] = variation
            else:
                variations.setdefault(variation.name, variation)

    return variations


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


def run_validators(value: FileLike, validators: Iterable[Any]):
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
