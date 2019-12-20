import time
from typing import IO, Dict, Any, Iterable, Union
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS
from django.core import exceptions
from django.core.files import File
from django.core.exceptions import ObjectDoesNotExist
from .logging import logger

MAX_DB_ATTEMPTS = 3


def run_validators(value: Union[IO, File], validators: Iterable[Any]):
    errors = []
    for v in validators:
        try:
            v(value)
        except exceptions.ValidationError as e:
            errors.extend(e.error_list)

    if errors:
        raise exceptions.ValidationError(errors)


def lowercase_copy(options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Возвращает копию словаря с ключами, приведенными к нижнему регистру.
    """
    return {
        key.lower(): value
        for key, value in options.items()
    }


def get_instance(app_label: str, model_name: str, object_id: int, using: str = DEFAULT_DB_ALIAS):
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
            if attempts > MAX_DB_ATTEMPTS:
                logger.exception('Instance #%s not found' % object_id)
                raise
            else:
                time.sleep(1)
