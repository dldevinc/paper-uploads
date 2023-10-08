import datetime
import re

re_suffix_pattern = re.compile(r"\{+\s*suffix\s*}+")
re_suffix = re.compile(r"(_\w{6,7})$")


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


def match_path(value: str, pattern: str, *, source: str = None):
    """
    Проверка соответствия пути `target` паттерну `pattern`.

    Паттерн может включать

    Для проверки наличия суффикса, добавляемого FileSystemStorage,
    требуется указать путь к исходному файлу `source`.

    Пример:
        match_path(
            "/media/2023/10/07/file_hUCd5n.jpg",
            "/media/%Y/%m/%d/file{suffix}.jpg",
        )
    """
    date = datetime.datetime.now()

    pattern_with_suffix = re_suffix_pattern.search(pattern)
    if not pattern_with_suffix:
        target = date.strftime(pattern)
        return value == target or value.endswith(target)

    before, after = re_suffix_pattern.split(pattern, maxsplit=1)
    before = date.strftime(before)
    after = date.strftime(after)
    if not value.endswith(after):
        return False

    value = value[:-len(after)]
    suffix_match = re_suffix.search(value)
    if suffix_match is not None:
        target = before + suffix_match.group(1)
    else:
        target = before

    return value == target or value.endswith(target)


def is_equal_dates(date1, date2, delta: int = 10):
    return abs((date2 - date1).seconds) < delta
