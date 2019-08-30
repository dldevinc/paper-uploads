import time
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from . import utils

MAX_DB_ATTEMPTS = 3


def _get_instance(app_label, model_name, object_id):
    model_class = apps.get_model(app_label, model_name)
    attempts = 1
    while True:
        try:
            return model_class._meta.base_manager.get(pk=object_id)
        except ObjectDoesNotExist:
            # delay recheck if transaction not commited yet
            attempts += 1
            if attempts > MAX_DB_ATTEMPTS:
                utils.logger.exception('Not found %s' % object_id)
                raise
            else:
                time.sleep(1)


def recut_image(app_label, model_name, object_id, names=None):
    instance = _get_instance(app_label, model_name, object_id)
    instance._recut_sync(names)


def recut_gallery(app_label, model_name, object_id, names=None):
    instance = _get_instance(app_label, model_name, object_id)
    instance._recut_sync(names)
