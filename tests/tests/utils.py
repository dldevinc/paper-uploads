import datetime
import os
import re

re_suffix = re.compile(r'(_[\w]{6,7})$')


def get_file_suffix(filepath: str) -> str:
    basename = os.path.basename(filepath)
    name, _ = os.path.splitext(basename)

    match = re_suffix.search(name)
    if match is not None:
        return match.group(1)
    return ''


def get_target_filepath(pattern: str, filepath: str) -> str:
    """
    Build filepath, similar to FileSystemStorage
    """
    value = datetime.datetime.now().strftime(pattern)
    suffix = get_file_suffix(filepath)
    value = value.format(
        suffix=suffix or ''
    )
    return value
