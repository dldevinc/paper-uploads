from typing import IO, Dict, Any, Iterable, Union
from django.core import exceptions
from django.core.files import File


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
