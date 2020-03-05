import time
from typing import IO, Any, Dict, Iterable, List, Union

from django.apps import apps
from django.core import exceptions
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db import DEFAULT_DB_ALIAS

from .logging import logger

MAX_DB_ATTEMPTS = 3


def remove_dulpicates(seq):
    """
    https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order
    """
    seen = set()
    seen_add = seen.add
    return tuple(x for x in seq if not (x in seen or seen_add(x)))


def run_validators(value: Union[IO, File], validators: Iterable[Any]):
    errors = []  # type: List[Any]
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
    return {key.lower(): value for key, value in options.items()}


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
            if attempts > MAX_DB_ATTEMPTS:
                logger.exception('Instance #%s not found' % object_id)
                raise
            else:
                time.sleep(1)
