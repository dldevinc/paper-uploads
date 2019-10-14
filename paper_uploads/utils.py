import os
import shutil
import posixpath
import subprocess
from typing import IO, Dict, Any, Iterable, Union
from django.core import exceptions
from django.core.files import File
from variations.variation import Variation
from .conf import settings
from .logging import logger
from .storage import upload_storage


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
    Имя файла может включать путь - он остается неизменным.
    """
    root, basename = posixpath.split(filename)
    filename, ext = posixpath.splitext(basename)
    filename = posixpath.extsep.join((filename, variation_name))
    basename = ''.join((filename, ext))
    path = posixpath.join(root, basename)
    return variation.replace_extension(path)


def _postprocess_file(path: str, command: Dict[str, str]):
    """
    Запуск консольной команды для постобработки файла.
    """
    command = {
        key.lower(): value
        for key, value in command.items()
    }

    executable = command.get('command')
    if not executable:
        return

    executable_path = shutil.which(executable)
    if executable_path is None:
        logger.warning("Command '{}' not found".format(executable))
        return

    arguments = command.get('arguments', '').format(
        file=path
    )
    process = subprocess.Popen(
        '{} {}'.format(executable_path, arguments),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True
    )
    out, err = process.communicate()
    logger.debug('Command: {} {}\nStdout: {}\nStderr: {}'.format(
        executable_path,
        arguments,
        out.decode() if out is not None else '',
        err.decode() if err is not None else '',
    ))


def postprocess_variation(source_filename: str, variation_name: str, variation: Variation, command: Dict[str, str] = None):
    """
    Постобработка файла вариации изображения.
    """
    variation_path = get_variation_filename(source_filename, variation_name, variation)
    full_path = upload_storage.path(variation_path)
    if not os.path.exists(full_path):
        logger.warning('File not found: {}'.format(variation_path))
        return

    output_format = variation.output_format(variation_path)
    variation_command = variation.extra_context.get(output_format.lower(), {}).get('postprocess', {})
    if variation_command is None:
        # обработка явным образом запрещена
        return

    global_command = getattr(settings, 'POSTPROCESS', {}).get(output_format, {})
    command = command or variation_command or global_command
    if command:
        _postprocess_file(full_path, command)


def postprocess_svg(source_filename: str, command: Dict[str, str] = None):
    """
    Постобработка SVG-файла.
    """
    full_path = upload_storage.path(source_filename)
    if not os.path.exists(full_path):
        logger.warning('File not found: {}'.format(full_path))
        return

    global_command = getattr(settings, 'POSTPROCESS', {}).get('SVG', {})
    command = command or global_command
    if command:
        _postprocess_file(full_path, command)
