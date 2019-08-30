import logging
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from variations.variation import Variation
from .conf import settings

logger = logging.getLogger('paper_uploads')


def build_variations(options):
    variations = {}
    for key, config in (options or {}).items():
        if settings.DEFAULT_FACE_DETECTION:
            config.setdefault('face_detection', True)
        variations[key] = Variation(**config)
    return variations


def get_field(app_label, model_name, fieldname):
    """
    Получение поля модели.
    """
    try:
        model_class = apps.get_model(app_label, model_name)
    except LookupError:
        logger.exception("Not found model: %s.%s" % (app_label, model_name))
        return

    try:
        return model_class._meta.get_field(fieldname)
    except FieldDoesNotExist:
        logger.exception("Not found field '%s' in model %s.%s" % (app_label, model_name, fieldname))
