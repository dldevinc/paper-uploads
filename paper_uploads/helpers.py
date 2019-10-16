from typing import Dict, Any
from variations.variation import Variation
from .conf import settings


def build_variations(options: Dict[str, Any]) -> Dict[str, Variation]:
    """
    Создание объектов вариаций из словаря конфигурации.
    """
    variations = {}
    for key, config in (options or {}).items():
        if settings.DEFAULT_FACE_DETECTION:
            config.setdefault('face_detection', True)
        variations[key] = Variation(**config)
    return variations
