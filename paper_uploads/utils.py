import hashlib
import re
from typing import Any, Dict, Iterable, Set, Tuple

from .typing import FileLike

filesize_regex = re.compile(r'^([.\d]+)\s*([KMGT])?B?$')
filesize_units = {"K": 2 ** 10, "M": 2 ** 20, "G": 2 ** 30, "T": 2 ** 40}


def checksum(file: FileLike) -> str:
    """
    DropBox checksum realization.
    https://www.dropbox.com/developers/reference/content-hash
    """
    if file.closed:
        file.open('rb')
    elif file.seekable():
        file.seek(0)

    blocks = []
    while True:
        data = file.read(4 * 1024 * 1024)
        if not data:
            break
        blocks.append(hashlib.sha256(data).digest())
    return hashlib.sha256(b''.join(blocks)).hexdigest()


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
