import os
import shutil
import posixpath
import subprocess
from typing import IO
from django.core import exceptions
from variations.variation import Variation
from .conf import settings
from .logging import logger
from .storage import upload_storage
from .typing import PostprocessOptions


def build_variations(options: dict) -> dict:
    """
    Создание объектов вариаций из словаря конфигурации.
    """
    variations = {}
    for key, config in (options or {}).items():
        if settings.DEFAULT_FACE_DETECTION:
            config.setdefault('face_detection', True)
        variations[key] = Variation(**config)
    return variations


def run_validators(value: IO, validators: list):
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


def _postprocess_file(path: str, options: PostprocessOptions):
    """
    Запуск консольной команды для постобработки файла.
    """
    options = {
        key.lower(): value
        for key, value in options.items()
    }

    command = options.get('command')
    if not command:
        return

    command_path = shutil.which(command)
    if command_path is None:
        logger.warning("Command '{}' not found".format(command))
        return

    arguments = options['arguments'].format(
        file=path
    )
    process = subprocess.Popen(
        '{} {}'.format(command_path, arguments),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True
    )
    out, err = process.communicate()
    logger.debug('Command: {} {}\nStdout: {}\nStderr: {}'.format(
        command_path,
        arguments,
        out.decode() if out is not None else '',
        err.decode() if err is not None else '',
    ))


def postprocess_variation(source_filename: str, variation_name: str, variation: Variation, options: PostprocessOptions = None):
    """
    Постобработка файла вариации изображения.
    """
    variation_path = get_variation_filename(source_filename, variation_name, variation)
    full_path = upload_storage.path(variation_path)
    if not os.path.exists(full_path):
        logger.warning('File not found: {}'.format(variation_path))
        return

    output_format = variation.output_format(variation_path)
    variation_options = variation.extra_context.get(output_format.lower(), {}).get('postprocess', {})
    if variation_options is None:
        # обработка явным образом запрещена
        return

    global_options = getattr(settings, 'POSTPROCESS', {}).get(output_format, {})
    postprocess_options = options or variation_options or global_options
    if postprocess_options:
        _postprocess_file(full_path, postprocess_options)


def postprocess_svg(source_filename: str, options: PostprocessOptions = None):
    """
    Постобработка SVG-файла.
    """
    full_path = upload_storage.path(source_filename)
    if not os.path.exists(full_path):
        logger.warning('File not found: {}'.format(full_path))
        return

    global_options = getattr(settings, 'POSTPROCESS', {}).get('SVG', {})

    postprocess_options = options or global_options
    if postprocess_options:
        _postprocess_file(full_path, postprocess_options)
