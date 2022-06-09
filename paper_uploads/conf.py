from copy import deepcopy
from typing import Dict, Iterable

from django import conf
from django.utils.module_loading import import_string

DEFAULTS = {
    "STORAGE": "django.core.files.storage.FileSystemStorage",
    "STORAGE_OPTIONS": {},
    "FILES_UPLOAD_TO": "files/%Y/%m/%d",
    "IMAGES_UPLOAD_TO": "images/%Y/%m/%d",
    "COLLECTION_FILES_UPLOAD_TO": "collections/files/%Y/%m/%d",
    "COLLECTION_IMAGES_UPLOAD_TO": "collections/images/%Y/%m/%d",
    "COLLECTION_ITEM_PREVIEW_WIDTH": 180,
    "COLLECTION_ITEM_PREVIEW_HEIGHT": 135,

    "RQ_ENABLED": False,
    "RQ_QUEUE_NAME": "default",
    "VARIATION_DEFAULTS": None,
}

# Иконки для файлов в галерее
FILE_ICON_DEFAULT = "unknown"
FILE_ICON_OVERRIDES = {
    "3gp": "video",
    "aac": "audio",
    "docx": "doc",
    "flac": "audio",
    "flv": "video",
    "gz": "archive",
    "jpeg": "jpg",
    "m4a": "audio",
    "m4v": "video",
    "mkv": "video",
    "mov": "video",
    "mpeg": "video",
    "ogg": "audio",
    "ogv": "video",
    "xlsx": "xls",
    "xz": "archive",
    "wav": "audio",
    "webm": "video",
    "wma": "audio",
    "wmv": "video",
}


class Settings:
    """
    A settings object, that allows API settings to be accessed as properties.
    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """

    def __init__(self, user_settings: Dict = None, defaults: Dict = None, import_strings: Iterable = None):
        self.user_settings = user_settings
        self.defaults = defaults
        self.import_strings = import_strings

    def __getstate__(self):
        return {
            "user_settings": self.user_settings,
            "defaults": self.defaults,
            "import_strings": self.import_strings,
        }

    def __getattr__(self, name):
        if name.startswith("prepare_"):
            raise AttributeError(name)

        self.__dict__[name] = value = self._get_value(name)
        return value

    def __copy__(self):
        clone = type(self)()
        clone.__dict__.update(
            user_settings=self.user_settings,
            defaults=self.defaults,
            import_strings=self.import_strings,
        )
        return clone

    def __deepcopy__(self, memo):
        clone = type(self)()
        memo[id(self)] = clone
        clone.user_settings = deepcopy(self.user_settings, memo)
        clone.defaults = deepcopy(self.defaults, memo)
        clone.import_strings = deepcopy(self.import_strings, memo)
        return clone

    def _get_value(self, name):
        value = self._fetch_value(name)

        # Coerce import strings into classes
        if name in self.import_strings:
            return self._perform_import(value, name)

        # Prepare value
        method_name = "prepare_{}".format(name.lower())
        prepare_method = getattr(self, method_name, None)
        if prepare_method is not None:
            value = prepare_method(value)

        return value

    def _fetch_value(self, name):
        try:
            # Check if present in user settings
            return self.user_settings[name]
        except KeyError:
            pass

        try:
            # Fall back to defaults
            return self.defaults[name]
        except KeyError:
            pass

        raise AttributeError("Invalid setting: '%s'" % name)

    @classmethod
    def _perform_import(cls, val, setting_name):
        """
        If the given setting is a string import notation,
        then perform the necessary import or imports.
        """
        if val is None:
            return
        elif isinstance(val, str):
            return cls._import_from_string(val, setting_name)
        elif isinstance(val, (list, tuple)):
            return [cls._import_from_string(item, setting_name) for item in val]
        return val

    @staticmethod
    def _import_from_string(val, setting_name):
        """
        Attempt to import a class from a string representation.
        """
        try:
            return import_string(val)
        except ImportError as e:
            msg = "Could not import '%s' for API setting '%s'. %s: %s." % (
                val,
                setting_name,
                e.__class__.__name__,
                e,
            )
            raise ImportError(msg)


settings = Settings(
    user_settings=getattr(conf.settings, "PAPER_UPLOADS", {}),
    defaults=DEFAULTS,
    import_strings={"STORAGE"}
)


IMAGE_ITEM_VARIATIONS = dict(
    admin_preview=dict(
        size=(
            settings.COLLECTION_ITEM_PREVIEW_WIDTH,
            settings.COLLECTION_ITEM_PREVIEW_HEIGHT
        ),
        format="jpeg",
        versions={"webp", "2x"},
        jpeg=dict(
            quality=75
        ),
        webp=dict(
            quality=65
        ),
    ),
)
