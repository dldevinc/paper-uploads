from typing import Any, Dict

from ... import validators


def validators_to_options(field_validators) -> Dict[str, Any]:
    """
    Превращает Django-валидаторы в словарь конфигурации,
    который может использоваться для вывода или проверки
    на стороне клиента.
    """
    config = {}
    for v in field_validators:
        if isinstance(v, validators.MimeTypeValidator):
            config["acceptFiles"] = v.allowed
        elif isinstance(v, validators.ExtensionValidator):
            config["allowedExtensions"] = v.allowed
        elif isinstance(v, validators.MaxSizeValidator):
            config["sizeLimit"] = v.limit_value
        elif isinstance(v, validators.ImageMinSizeValidator):
            config["minImageWidth"] = v.width_limit
            config["minImageHeight"] = v.height_limit
        elif isinstance(v, validators.ImageMaxSizeValidator):
            config["maxImageWidth"] = v.width_limit
            config["maxImageHeight"] = v.height_limit

    return config
