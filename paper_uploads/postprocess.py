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


def get_options(format: str, field: Any = None, variation: PaperVariation = None) -> Dict[str, str]:
    """
    Получение настроек постобработки для заданного формата.
    Если постобработка запрещена, выбрасывает исключение PostprocessProhibited.

    Порядок проверки:
    1) опция `postprocess` для конкретного формата вариации
    2) опция `postprocess` вариации
    3) поле (FileField или CollectionItemTypeField)
    4) настройка `PAPER_UPLOADS['POSTPROCESS']`
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

    if field is not None:
        field_options = getattr(field, 'postprocess', None)
        if field_options is False:
            raise PostprocessProhibited
        elif field_options:
            return lowercase_copy(field_options)

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


def postprocess_variation(source_filename: str, variation: PaperVariation,
        options: Dict[str, str] = None):
    """
    Постобработка файла вариации изображения.
    """
    if options is False:
        return

    variation_filename = variation.get_output_filename(source_filename)
    variation_path = upload_storage.path(variation_filename)
    if not os.path.exists(variation_path):
        logger.warning('File not found: {}'.format(variation_path))
        return

    output_format = variation.output_format(variation_filename)

    try:
        postprocess_options = get_options(output_format, variation=variation)
    except PostprocessProhibited:
        return

    if options:
        postprocess_options.update(options)
    _postprocess_file(variation_path, postprocess_options)


def postprocess_uploaded_file(source_filename: str, field: Any = None,
        options: Dict[str, str] = None):
    """
    Постобработка загруженного файла.
    """
    if options is False:
        return

    full_path = upload_storage.path(source_filename)
    if not os.path.exists(full_path):
        logger.warning('File not found: {}'.format(full_path))
        return

    _, ext = os.path.splitext(source_filename)
    ext = ext.lower()
    if ext in Image.EXTENSION.keys():
        # файл является изображением — их не трогаем
        return

    try:
        postprocess_options = get_options(ext.lstrip('.'), field=field)
    except PostprocessProhibited:
        return

    if field is not None and field.postprocess:
        postprocess_options.update(lowercase_copy(field.postprocess))
    if options:
        postprocess_options.update(options)
    _postprocess_file(full_path, postprocess_options)
