import os
import shutil
import posixpath
import subprocess
from django.core import exceptions
from variations.variation import Variation
from .conf import settings
from .logging import logger
from .storage import upload_storage


def build_variations(options):
    """
    Создание объектов вариаций из словаря конфигурации.

    :type options: dict
    :rtype: dict
    """
    variations = {}
    for key, config in (options or {}).items():
        if settings.DEFAULT_FACE_DETECTION:
            config.setdefault('face_detection', True)
        variations[key] = Variation(**config)
    return variations


def run_validators(value, validators):
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


def postprocess_variation(source_filename, variation_name, variation, options=None):
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
    if not postprocess_options:
        return

    # fix case
    postprocess_options = {
        key.lower(): value
        for key, value in postprocess_options.items()
    }

    command = postprocess_options.get('command')
    if not command:
        return

    command_path = shutil.which(command)
    if command_path is None:
        logger.warning("Command '{}' not found".format(command))
        return

    root, filename = os.path.split(full_path)
    arguments = postprocess_options['arguments'].format(
        dir=root,
        filename=filename,
        file=full_path
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


def postprocess_svg(source_filename, options=None):
    full_path = upload_storage.path(source_filename)
    if not os.path.exists(full_path):
        logger.warning('File not found: {}'.format(full_path))
        return

    global_options = getattr(settings, 'POSTPROCESS', {}).get('SVG', {})

    postprocess_options = options or global_options
    if not postprocess_options:
        return

    # fix case
    postprocess_options = {
        key.lower(): value
        for key, value in postprocess_options.items()
    }

    command = postprocess_options.get('command')
    if not command:
        return

    command_path = shutil.which(command)
    if command_path is None:
        logger.warning("Command '{}' not found".format(command))
        return

    root, filename = os.path.split(full_path)
    arguments = postprocess_options['arguments'].format(
        dir=root,
        filename=filename,
        file=full_path
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
