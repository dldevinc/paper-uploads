from variations.variation import Variation
from .conf import settings


def build_variations(options):
    variations = {}
    for key, config in (options or {}).items():
        if settings.DEFAULT_FACE_DETECTION:
            config.setdefault('face_detection', True)
        variations[key] = Variation(**config)
    return variations
