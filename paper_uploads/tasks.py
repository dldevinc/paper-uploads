import time
from typing import Iterable, Dict
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS
from django.core.exceptions import ObjectDoesNotExist
from . logging import logger

MAX_DB_ATTEMPTS = 3


def _get_instance(app_label: str, model_name: str, object_id: int, using: str = DEFAULT_DB_ALIAS):
    """
    Получение экземпляра модели по названию приложения, модели и ID.
    """
    model_class = apps.get_model(app_label, model_name)
    attempts = 1
    while True:
        try:
            return model_class._base_manager.using(using).get(pk=object_id)
        except ObjectDoesNotExist:
            # delay recheck if transaction not commited yet
            attempts += 1
            if attempts > MAX_DB_ATTEMPTS:
                logger.exception('Not found instance #%s' % object_id)
                raise
            else:
                time.sleep(1)


def recut_image(app_label: str, model_name: str, object_id: int,
        names: Iterable[str] = None, using: str = DEFAULT_DB_ALIAS,
        postprocess: Dict[str, str] = None):
    instance = _get_instance(app_label, model_name, object_id, using=using)
    instance._recut_sync(names, postprocess=postprocess)


def recut_collection(app_label: str, model_name: str, object_id: int,
        names: Iterable[str] = None, using: str = DEFAULT_DB_ALIAS,
        postprocess: Dict[str, str] = None):
    collection = _get_instance(app_label, model_name, object_id, using=using)
    collection._recut_sync(names, using=using, postprocess=postprocess)
