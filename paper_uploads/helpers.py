from typing import Dict, Any
from .conf import settings
from .utils import lowercase_copy
from .variations import PaperVariation


def create_webp_version(config: Dict[str, Any]):
    version_config = dict(config, format='webp')
    return PaperVariation(**version_config)


def create_retina_version(config: Dict[str, Any], *, factor=2):
    varaition_size = config.get('size', (0, 0))
    version_size = tuple(x * factor for x in varaition_size)
    version_config = dict(config, size=version_size)
    return PaperVariation(**version_config)


def get_addition_versions(name: str, config: Dict[str, Any], variation: PaperVariation):
    addition_variations = {}
    need_webp_version = 'webp' in variation.versions and variation.format != 'WEBP'

    def add_retina_versions(factor: int):
        version_name = '{}_{}x'.format(name, factor)
        addition_variations[version_name] = create_retina_version(config, factor=factor)
        if need_webp_version:
            version_name = '{}_webp_{}x'.format(name, factor)
            addition_variations[version_name] = create_webp_version(config)

    if '2x' in variation.versions:
        add_retina_versions(2)
    if '3x' in variation.versions:
        add_retina_versions(3)
    if '4x' in variation.versions:
        add_retina_versions(4)
    if need_webp_version:
        version_name = '{}_webp'.format(name)
        addition_variations[version_name] = create_webp_version(config)
    return addition_variations


def build_variations(options: Dict[str, Any]) -> Dict[str, PaperVariation]:
    """
    Создание объектов вариаций из словаря конфигурации.
    """
    variations = {}
    for vname, config in options.items():
        new_config = lowercase_copy(settings.VARIATION_DEFAULTS)
        new_config.update(config)
        new_config['name'] = vname

        variations[vname] = variation = PaperVariation(**new_config)
        additional_variations = get_addition_versions(vname, new_config, variation)
        for name, version in additional_variations.items():
            variations.setdefault(name, version)

    return variations
