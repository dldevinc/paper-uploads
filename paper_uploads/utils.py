import posixpath
from typing import IO, Dict, Any, Iterable, Union
from django.core import exceptions
from django.core.files import File
from variations.variation import Variation


def run_validators(value: Union[IO, File], validators: Iterable[Any]):
    errors = []
    for v in validators:
        try:
            v(value)
        except exceptions.ValidationError as e:
            errors.extend(e.error_list)

    if errors:
        raise exceptions.ValidationError(errors)


def get_variation_filename(filename: str, variation_name: str, variation: Variation) -> str:
    """
    Конструирует имя файла для вариации по имени файла исходника.
    Имя файла может включать путь — он остается неизменным.
    """
    root, basename = posixpath.split(filename)
    filename, ext = posixpath.splitext(basename)
    filename = posixpath.extsep.join((filename, variation_name))
    basename = ''.join((filename, ext))
    path = posixpath.join(root, basename)
    return variation.replace_extension(path)


def lowercase_copy(options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Возвращает копию словаря с ключами, приведенными к нижнему регистру.
    """
    return {
        key.lower(): value
        for key, value in options.items()
    }
