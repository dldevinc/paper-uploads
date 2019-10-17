from typing import Dict, Any
from variations.variation import Variation
from .conf import settings
from .utils import lowercase_copy


def build_variations(options: Dict[str, Any]) -> Dict[str, Variation]:
    """
    Создание объектов вариаций из словаря конфигурации.
    """
    variations = {}
    for key, config in options.items():
        new_config = lowercase_copy(settings.VARIATION_DEFAULTS)
        new_config.update(config)
        variations[key] = Variation(**new_config)
    return variations
