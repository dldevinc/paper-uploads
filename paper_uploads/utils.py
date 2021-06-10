import hashlib
import re
from typing import Any, Dict, Iterable, Set, Tuple

from django.utils import formats
from django.utils.html import avoid_wrapping
from django.utils.translation import gettext, ngettext

from .typing import FileLike

filesize_regex = re.compile(r"^([.\d]+)\s*([KMGT])?B?$")
filesize_units = {"K": 10 ** 3, "M": 10 ** 6, "G": 10 ** 9, "T": 10 ** 12}


def checksum(file: FileLike) -> str:
    """
    DropBox checksum realization.
    https://www.dropbox.com/developers/reference/content-hash
    """
    if file.closed:
        file.open("rb")
    elif file.seekable():
        file.seek(0)

    blocks = []
    while True:
        data = file.read(4 * 1024 * 1024)
        if not data:
            break
        blocks.append(hashlib.sha256(data).digest())
    return hashlib.sha256(b"".join(blocks)).hexdigest()


def remove_dulpicates(seq: Iterable) -> Tuple:
    """
    https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order
    """
    seen = set()  # type: Set[Any]
    seen_add = seen.add
    return tuple(x for x in seq if not (x in seen or seen_add(x)))


def lowercased_dict_keys(options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Возвращает копию словаря с ключами, приведенными к нижнему регистру.
    """
    return {key.lower(): value for key, value in options.items()}


def parse_filesize(value: str) -> int:
    """
    Парсинг человеко-понятного значения размера файла.
    Допустимые форматы значения: 4k, 4kb, 4KB, 4 K, 4 Kb
    """
    match = filesize_regex.match(value.upper().strip())
    number, unit = match.groups()
    return int(float(number) * filesize_units.get(unit, 1))


def filesizeformat(bytes_: int) -> str:
    """
    Форматирование размера файла.
    В отличие от одноименной встроенной функции, выводит настоящие килобайты/мегабайты,
    вместо кибибайтов/мибибайтов.
    """
    try:
        bytes_ = float(bytes_)
    except (TypeError, ValueError, UnicodeDecodeError):
        value = ngettext("%(size)d byte", "%(size)d bytes", 0) % {'size': 0}
        return avoid_wrapping(value)

    def filesize_number_format(value):
        return formats.number_format(round(value, 1), 1)

    KB = 10 ** 3
    MB = 10 ** 6
    GB = 10 ** 9
    TB = 10 ** 12
    PB = 10 ** 15

    negative = bytes_ < 0
    if negative:
        bytes_ = -bytes_  # Allow formatting of negative numbers.

    if bytes_ < KB:
        value = ngettext("%(size)d byte", "%(size)d bytes", bytes_) % {'size': bytes_}
    elif bytes_ < MB:
        value = gettext("%s KB") % filesize_number_format(bytes_ / KB)
    elif bytes_ < GB:
        value = gettext("%s MB") % filesize_number_format(bytes_ / MB)
    elif bytes_ < TB:
        value = gettext("%s GB") % filesize_number_format(bytes_ / GB)
    elif bytes_ < PB:
        value = gettext("%s TB") % filesize_number_format(bytes_ / TB)
    else:
        value = gettext("%s PB") % filesize_number_format(bytes_ / PB)

    if negative:
        value = "-%s" % value
    return avoid_wrapping(value)
