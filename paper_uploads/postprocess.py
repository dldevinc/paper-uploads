import os
import shutil
import subprocess
from PIL import Image
from typing import Dict, Any
from .conf import settings
from .logging import logger
from .storage import upload_storage
from .exceptions import PostprocessProhibited
from .utils import lowercase_copy
from .variations import PaperVariation


def _run(path: str, options: Dict[str, str]):
    """
    Запуск консольной команды над файлом.
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


def get_postprocess_variation_options(format: str, variation: PaperVariation, field: Any = None) -> Dict[str, str]:
    """
    Получение настроек постобработки изображения для заданного формата.
    Если постобработка запрещена, выбрасывает исключение PostprocessProhibited.
    """
    format = format.lower()

    variation_options = variation.get_postprocess_options(format)
    if variation_options is False:
        raise PostprocessProhibited
    elif variation_options is not None:
        return lowercase_copy(variation_options)

    if field is not None:
        field_options = getattr(field, 'postprocess', None)
        if field_options is False:
            raise PostprocessProhibited
        elif field_options is not None:
            field_format_options = field_options.get(format)
            if field_format_options is False:
                raise PostprocessProhibited
            elif field_format_options is not None:
                return lowercase_copy(field_format_options)

    global_options = getattr(settings, 'POSTPROCESS', {})
    if global_options is False:
        raise PostprocessProhibited
    elif global_options is not None:
        global_format_options = global_options.get(format)
        if global_format_options is False:
            raise PostprocessProhibited
        elif global_format_options is not None:
            return lowercase_copy(global_format_options)

    raise PostprocessProhibited


def postprocess_variation(variation_filename: str, variation: PaperVariation,
        field: Any = None):
    """
    Постобработка загруженного изображения.
    """
    variation_path = upload_storage.path(variation_filename)
    if not os.path.exists(variation_path):
        logger.warning('File not found: {}'.format(variation_path))
        return

    output_format = variation.output_format(variation_path)

    try:
        postprocess_options = get_postprocess_variation_options(
            output_format,
            variation,
            field=field
        )
    except PostprocessProhibited:
        return
    _run(variation_path, postprocess_options)


def get_postprocess_common_options(format: str, field: Any = None) -> Dict[str, str]:
    """
    Получение настроек постобработки файла для заданного формата.
    Если постобработка запрещена, выбрасывает исключение PostprocessProhibited.
    """
    format = format.lower()

    if field is not None:
        field_options = getattr(field, 'postprocess', None)
        if field_options is False:
            raise PostprocessProhibited
        elif field_options is not None:
            field_format_options = field_options.get(format)
            if field_format_options is False:
                raise PostprocessProhibited
            elif field_format_options is not None:
                return lowercase_copy(field_format_options)

    global_options = getattr(settings, 'POSTPROCESS', {})
    if global_options is False:
        raise PostprocessProhibited
    elif global_options is not None:
        global_format_options = global_options.get(format)
        if global_format_options is False:
            raise PostprocessProhibited
        elif global_format_options is not None:
            return lowercase_copy(global_format_options)

    raise PostprocessProhibited


def postprocess_common_file(source_filename: str, field: Any = None):
    """
    Постобработка загруженного файла.
    """
    source_path = upload_storage.path(source_filename)
    if not os.path.exists(source_path):
        logger.warning('File not found: {}'.format(source_path))
        return

    _, ext = os.path.splitext(source_filename)
    ext = ext.lower()
    if ext in Image.EXTENSION.keys():
        # файл является изображением — их не трогаем
        return

    try:
        postprocess_options = get_postprocess_common_options(ext.lstrip('.'), field=field)
    except PostprocessProhibited:
        return
    _run(source_path, postprocess_options)
