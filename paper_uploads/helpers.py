from typing import Dict, Any
from .conf import settings
from .utils import lowercase_copy
from .variations import PaperVariation


def build_variations(options: Dict[str, Any]) -> Dict[str, PaperVariation]:
    """
    Создание объектов вариаций из словаря конфигурации.
    """
    variations = {}
    for vname, config in options.items():
        new_config = lowercase_copy(settings.VARIATION_DEFAULTS)
        new_config.update(config)
        new_config['name'] = vname
        variations[vname] = PaperVariation(**new_config)
    return variations
