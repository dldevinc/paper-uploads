from django import conf
from django.utils.module_loading import import_string


DEFAULTS = {
    'STORAGE': 'django.core.files.storage.FileSystemStorage',
    'STORAGE_OPTIONS': {},

    'FILES_UPLOAD_TO': 'files/%Y-%m-%d',
    'IMAGES_UPLOAD_TO': 'images/%Y-%m-%d',
    'GALLERY_FILES_UPLOAD_TO': 'gallery/files/%Y-%m-%d',
    'GALLERY_IMAGES_UPLOAD_TO': 'gallery/images/%Y-%m-%d',

    'GALLERY_ITEM_PREVIEW_WIDTH': 144,
    'GALLERY_ITEM_PREVIEW_HEIGTH': 108,
    'GALLERY_IMAGE_ITEM_PREVIEW_VARIATIONS': dict(
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
                quality=84
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

    'DEFAULT_FACE_DETECTION': False,

    'RQ_ENABLED': False,
    'RQ_QUEUE_NAME': 'default',

    'POSTPROCESS': {},
}

# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    'STORAGE',
)


# Атрибуты файла, переносимые на уровень модели
PROXY_FILE_ATTRIBUTES = {
    'url', 'path', 'open', 'read', 'close', 'closed'
}

# Иконки для файлов в галерее
FILE_ICON_DEFAULT = 'unknown'
FILE_ICON_OVERRIDES = {
    '3gp': 'video',
    'aac': 'audio',
    'docx': 'doc',
    'flac': 'audio',
    'flv': 'video',
    'gz': 'archive',
    'm4v': 'video',
    'mov': 'video',
    'ogv': 'video',
    'xlsx': 'xls',
    'xz': 'archive',
    'wav': 'audio',
    'wma': 'audio',
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
        if name not in self.defaults:
            raise AttributeError("Invalid setting: '%s'" % name)

        try:
            # Check if present in user settings
            val = self.user_settings[name]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[name]

        # Coerce import strings into classes
        if name in self.import_strings:
            val = perform_import(val, name)

        self.__dict__[name] = val
        return val


settings = Settings(
    getattr(conf.settings, 'PAPER_UPLOADS', {}),
    DEFAULTS,
    IMPORT_STRINGS
)
