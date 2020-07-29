from typing import Any, Dict, Iterable, Set, Tuple


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
