import os
import shutil
import subprocess
from typing import Dict
from variations.variation import Variation
from .conf import settings
from .logging import logger
from .storage import upload_storage
from .exceptions import PostprocessProhibited
from .utils import lowercase_copy, get_variation_filename


def get_options(format: str, variation: Variation = None) -> Dict[str, str]:
    """
    Получение настроек постобработки для заданного формата.
    Если постобработка запрещена, выбрасывает исключение PostprocessProhibited.

    Порядок проверки:
    1) опция `postprocess` для конкретного формата вариации
    2) опция `postprocess` вариации
    3) настройка `PAPER_UPLOADS['POSTPROCESS']`
    """
    format = format.lower()
    if variation is not None:
        variation_format_options = variation.extra_context.get(format, {}).get('postprocess', {})
        if variation_format_options is False:
            raise PostprocessProhibited
        elif variation_format_options:
            return lowercase_copy(variation_format_options)

        variation_options = variation.extra_context.get('postprocess', {})
        if variation_options is False:
            raise PostprocessProhibited
        elif variation_options:
            return lowercase_copy(variation_options)

    global_options = getattr(settings, 'POSTPROCESS', {})
    if global_options is False:
        raise PostprocessProhibited

    global_format_options = global_options.get(format, {})
    if global_format_options is False:
        raise PostprocessProhibited
    elif global_format_options:
        return lowercase_copy(global_format_options)

    return {}


def _postprocess_file(path: str, options: Dict[str, str]):
    """
    Запуск консольной команды для постобработки файла.
    """
    executable = options.get('command')
    if not executable:
        return

    executable_path = shutil.which(executable)
    if executable_path is None:
        logger.warning("Command '{}' not found".format(executable))
        return

    arguments = options.get('arguments', '').format(
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


def postprocess_variation(source_filename: str, variation_name: str, variation: Variation,
        options: Dict[str, str] = None):
    """
    Постобработка файла вариации изображения.
    """
    variation_path = get_variation_filename(source_filename, variation_name, variation)
    full_path = upload_storage.path(variation_path)
    if not os.path.exists(full_path):
        logger.warning('File not found: {}'.format(variation_path))
        return

    output_format = variation.output_format(variation_path)

    try:
        postprocess_options = get_options(output_format, variation)
    except PostprocessProhibited:
        return

    if options:
        postprocess_options.update(options)
    _postprocess_file(full_path, postprocess_options)


def postprocess_svg(source_filename: str, options: Dict[str, str] = None):
    """
    Постобработка SVG-файла.
    """
    full_path = upload_storage.path(source_filename)
    if not os.path.exists(full_path):
        logger.warning('File not found: {}'.format(full_path))
        return

    try:
        postprocess_options = get_options('svg')
    except PostprocessProhibited:
        return

    if options:
        postprocess_options.update(options)
    _postprocess_file(full_path, postprocess_options)
