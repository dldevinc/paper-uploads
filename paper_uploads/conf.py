from django import conf
from django.utils.module_loading import import_string


DEFAULTS = {
    'STORAGE': 'django.core.files.storage.FileSystemStorage',
    'STORAGE_OPTIONS': {},

    'FILES_UPLOAD_TO': 'files/%Y-%m-%d',
    'IMAGES_UPLOAD_TO': 'images/%Y-%m-%d',
    'COLLECTION_FILES_UPLOAD_TO': 'collections/files/%Y-%m-%d',
    'COLLECTION_IMAGES_UPLOAD_TO': 'collections/images/%Y-%m-%d',

    'COLLECTION_ITEM_PREVIEW_WIDTH': 144,
    'COLLECTION_ITEM_PREVIEW_HEIGTH': 108,
    'COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS': dict(
        admin_preview=dict(
            size=(144, 108),
            format='jpeg',
            jpeg=dict(
                quality=88
            ),
        ),
        admin_preview_2x=dict(
            size=(288, 216),
            format='jpeg',
            jpeg=dict(
                quality=85
            ),
        ),
        admin_preview_webp=dict(
            size=(144, 108),
            format='webp',
            webp=dict(
                quality=75
            ),
        ),
        admin_preview_webp_2x=dict(
            size=(288, 216),
            format='webp',
            webp=dict(
                quality=60
            ),
        ),
    ),

    'RQ_ENABLED': False,
    'RQ_QUEUE_NAME': 'default',

    'VARIATION_DEFAULTS': {},
    'POSTPROCESS': {},
}

# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    'STORAGE',
)

# Иконки для файлов в галерее
FILE_ICON_DEFAULT = 'unknown'
FILE_ICON_OVERRIDES = {
    '3gp': 'video',
    'aac': 'audio',
    'docx': 'doc',
    'flac': 'audio',
    'flv': 'video',
    'gz': 'archive',
    'm4a': 'audio',
    'm4v': 'video',
    'mkv': 'video',
    'mov': 'video',
    'ogg': 'audio',
    'ogv': 'video',
    'xlsx': 'xls',
    'xz': 'archive',
    'wav': 'audio',
    'webm': 'video',
    'wma': 'audio',
    'wmv': 'video',
}


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Could not import '%s' for API setting '%s'. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class Settings:
    """
    A settings object, that allows API settings to be accessed as properties.
    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """
    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        self.user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS

    def __getattr__(self, name):
        value = self._get_value(name)
        method_name = 'prepare_{}'.format(name.lower())
        prepare_method = getattr(self, method_name, None)
        if prepare_method is not None:
            value = prepare_method(value)
        self.__dict__[name] = value
        return value

    def _get_value(self, name):
        if name not in self.defaults:
            raise AttributeError("Invalid setting: '%s'" % name)

        try:
            # Check if present in user settings
            value = self.user_settings[name]
        except KeyError:
            # Fall back to defaults
            value = self.defaults[name]

        # Coerce import strings into classes
        if name in self.import_strings:
            return perform_import(value, name)
        return value

    def prepare_postprocess(self, value):
        from .utils import lowercase_copy
        return lowercase_copy(value)


settings = Settings(
    getattr(conf.settings, 'PAPER_UPLOADS', {}),
    DEFAULTS,
    IMPORT_STRINGS
)
