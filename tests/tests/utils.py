import datetime
import os
import re

re_suffix = re.compile(r'(_[\w]{6,7})$')


def compare_dicts(dict1, dict2, ignore=None):
    """
    Сравнение двух словарей с опциональным исключением определённых ключей.
    """
    ignore = ignore or set()

    if not ignore:
        assert dict1 == dict2
        return

    assert {
        k: v
        for k, v in dict1.items()
        if k not in ignore
    } == {
        k: v
        for k, v in dict2.items()
        if k not in ignore
    }


def get_file_suffix(filepath: str) -> str:
    basename = os.path.basename(filepath)
    name, _ = os.path.splitext(basename)

    match = re_suffix.search(name)
    if match is not None:
        return match.group(1)
    return ""


def match_path(target: str, pattern: str, *, source: str = None):
    """
    Проверка соответствия пути target паттерну pattern.
    Для проверки наличия суффикса, добавляемого FileSystemStorage,
    требуется указать путь к исходному файлу source.
    """
    value = datetime.datetime.now().strftime(pattern)

    if source:
        value = value.format(
            suffix=get_file_suffix(source)
        )
    else:
        value = value.format(
            suffix=get_file_suffix(target)
        )

    return target == value or target.endswith(value)


def is_equal_dates(date1, date2, delta=5):
    return abs((date2 - date1).seconds) < delta
