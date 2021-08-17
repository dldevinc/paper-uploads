import os
from typing import Sequence, Union

import magic
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from PIL import Image

from .typing import FileLike
from .utils import filesizeformat, parse_filesize, remove_dulpicates

__all__ = [
    "ExtensionValidator",
    "MimeTypeValidator",
    "SizeValidator",
    "ImageMinSizeValidator",
    "ImageMaxSizeValidator",
]


@deconstructible
class ExtensionValidator:
    message = _("File `%(name)s` has an invalid extension. Valid extension(s): %(allowed)s")
    code = "invalid_extension"

    def __init__(self, allowed: Sequence[str], message=None):
        self.allowed = remove_dulpicates(ext.lstrip(".").lower() for ext in allowed)
        if message:
            self.message = message

    def __call__(self, file: FileLike):
        _, ext = os.path.splitext(file.name)
        ext = ext.lstrip(".").lower()
        params = {
            "name": file.name,
            "ext": ext,
            "allowed": ", ".join(self.allowed),
        }
        if ext not in self.allowed:
            raise ValidationError(self.message, code=self.code, params=params)

    def get_help_text(self):
        return "{}: {}".format(_("Allowed extensions"), ", ".join(self.allowed))


@deconstructible
class MimeTypeValidator:
    message = _("File `%(name)s` has an invalid mimetype '%(mimetype)s'")
    code = "invalid_mimetype"

    def __init__(self, allowed: Sequence[str], message=None):
        self.allowed = remove_dulpicates(mime.lower() for mime in allowed)
        if message:
            self.message = message

    def __call__(self, file: FileLike):
        file.seek(0)  # ensure read from the start
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # correct file position after mimetype detection
        basetype, subtype = mimetype.split("/", 1)
        params = {
            "name": file.name,
            "mimetype": mimetype,
            "allowed": ", ".join(self.allowed),
        }
        if not (mimetype in self.allowed or "{}/*".format(basetype) in self.allowed):
            raise ValidationError(self.message, code=self.code, params=params)

    def get_help_text(self):
        return "{}: {}".format(_("Allowed types"), ", ".join(self.allowed))


@deconstructible
class SizeValidator:
    message = _("File `%(name)s` is too large. Maximum file size is %(limit_value)s.")
    code = "size_limit"

    def __init__(self, limit_value: Union[int, str], message=None):
        if isinstance(limit_value, str):
            self.limit_value = parse_filesize(limit_value)
        else:
            self.limit_value = limit_value

        if message:
            self.message = message

    def __call__(self, file: FileLike):
        params = {
            "name": file.name,
            "size": file.size,
            "limit_value": filesizeformat(self.limit_value),
        }
        if file.size > self.limit_value:
            raise ValidationError(self.message, code=self.code, params=params)

    def get_help_text(self):
        return "{}: {}".format(_("Maximum file size"), filesizeformat(self.limit_value))


@deconstructible
class ImageMinSizeValidator:
    error_messages = {
        "min_width": _(
            "Image `%(name)s` is not wide enough. The minimum width is %(width_limit)s pixels."
        ),
        "min_height": _(
            "Image `%(name)s` is not tall enough. The minimum height is %(height_limit)s pixels."
        ),
        "min_size": _(
            "Image `%(name)s` is too small. Image should be at least %(width_limit)sx%(height_limit)s pixels."
        ),
    }

    def __init__(self, width: int = 0, height: int = 0):
        self.width_limit = width
        self.height_limit = height

    def __call__(self, file: FileLike):
        if file.closed:
            raise ValidationError("File `%(name)s` is closed" % {"name": os.path.basename(file.name)})

        try:
            img = Image.open(file)
            image_size = img.size
        except OSError:
            raise ValidationError("File `%(name)s` is not an image" % {"name": os.path.basename(file.name)})

        params = {
            "width_limit": self.width_limit,
            "height_limit": self.height_limit,
            "size": image_size,
            "name": file.name,
        }

        invalid_width = self.width_limit and image_size[0] < self.width_limit
        invalid_height = self.height_limit and image_size[1] < self.height_limit
        if invalid_width:
            if invalid_height:
                code = "min_size"
            else:
                code = "min_width"
        elif invalid_height:
            code = "min_height"
        else:
            return

        raise ValidationError(self.error_messages[code], code=code, params=params)

    def get_help_text(self):
        if self.width_limit:
            if self.height_limit:
                return "{}: {}".format(
                    _("Minimum dimensions"),
                    _("%sx%s pixels") % (self.width_limit, self.height_limit)
                )
            else:
                return "{}: {}".format(_("Minimum image width"), _("%s pixels") % self.width_limit)
        elif self.height_limit:
            return "{}: {}".format(_("Minimum image height"), _("%s pixels") % self.height_limit)


@deconstructible
class ImageMaxSizeValidator:
    error_messages = {
        "max_width": _(
            "Image `%(name)s` is too wide. The maximum width is %(width_limit)s pixels."
        ),
        "max_height": _(
            "Image `%(name)s` is too tall. The maximum height is %(height_limit)s pixels."
        ),
        "max_size": _(
            "Image `%(name)s` is too big. Image should be at most %(width_limit)sx%(height_limit)s pixels."
        ),
    }

    def __init__(self, width: int = 0, height: int = 0):
        self.width_limit = width
        self.height_limit = height

    def __call__(self, file: FileLike):
        if file.closed:
            raise ValidationError("File `%(name)s` is closed" % {"name": os.path.basename(file.name)})

        try:
            img = Image.open(file)
            image_size = img.size
        except OSError:
            raise ValidationError("File `%(name)s` is not an image" % {"name": os.path.basename(file.name)})

        params = {
            "width_limit": self.width_limit,
            "height_limit": self.height_limit,
            "size": image_size,
            "name": file.name,
        }

        invalid_width = self.width_limit and image_size[0] > self.width_limit
        invalid_height = self.height_limit and image_size[1] > self.height_limit
        if invalid_width:
            if invalid_height:
                code = "max_size"
            else:
                code = "max_width"
        elif invalid_height:
            code = "max_height"
        else:
            return

        raise ValidationError(self.error_messages[code], code=code, params=params)

    def get_help_text(self):
        if self.width_limit:
            if self.height_limit:
                return "{}: {}".format(
                    _("Maximum dimensions"),
                    _("%sx%s pixels") % (self.width_limit, self.height_limit),
                )
            else:
                return "{}: {}".format(_("Maximum image width"), _("%s pixels") % self.width_limit)
        elif self.height_limit:
            return "{}: {}".format(_("Maximum image height"), _("%s pixels") % self.height_limit)
