import os
import magic
from typing import Sequence
from PIL import Image
from django.core.files import File
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat

__all__ = [
    'ExtensionValidator', 'MimetypeValidator', 'SizeValidator',
    'ImageMinSizeValidator', 'ImageMaxSizeValidator'
]


class HelpTextValidatorMixin:
    def get_help_text(self):
        raise NotImplementedError


@deconstructible
class ExtensionValidator(HelpTextValidatorMixin):
    message = _("`%(name)s` has an invalid extension. Valid extension(s): %(allowed)s")
    code = 'invalid_extension'

    def __init__(self, allowed: Sequence[str], message=None):
        self.allowed = tuple(ext.lstrip('.').lower() for ext in allowed)
        if message:
            self.message = message

    def __call__(self, file: File):
        _, ext = os.path.splitext(file.name)
        ext = ext.lstrip('.').lower()
        params = {
            'allowed': "'%s'" % "', '".join(self.allowed),
            'name': file.name
        }
        if ext not in self.allowed:
            raise ValidationError(self.message, code=self.code, params=params)

    def get_help_text(self):
        return _('Allowed extensions: {}'.format(", ".join(self.allowed)))


@deconstructible
class MimetypeValidator(HelpTextValidatorMixin):
    message = _("`%(name)s` has an invalid mimetype '%(mimetype)s'")
    code = 'invalid_mimetype'

    def __init__(self, allowed: Sequence[str], message=None):
        self.allowed = tuple(mime.lower() for mime in allowed)
        if message:
            self.message = message

    def __call__(self, file: File):
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # correct file position after mimetype detection
        basetype, subtype = mimetype.split('/', 1)
        params = {
            'allowed': "'%s'" % "', '".join(self.allowed),
            'mimetype': mimetype,
            'name': file.name
        }
        if not (mimetype in self.allowed or '{}/*'.format(basetype) in self.allowed):
            raise ValidationError(self.message, code=self.code, params=params)

    def get_help_text(self):
        return _('Allowed MIME types: {}'.format(", ".join(self.allowed)))


@deconstructible
class SizeValidator(HelpTextValidatorMixin):
    message = _("`%(name)s` is too large. Maximum file size is %(limit_value)s.")
    code = 'size_limit'

    def __init__(self, limit_value: int, message=None):
        self.limit_value = limit_value
        if message:
            self.message = message

    def __call__(self, file: File):
        params = {
            'limit_value': filesizeformat(self.limit_value),
            'size': file.size,
            'name': file.name
        }
        if file.size > self.limit_value:
            raise ValidationError(self.message, code=self.code, params=params)

    def get_help_text(self):
        return _('Maximum file size: {}'.format(filesizeformat(self.limit_value)))


@deconstructible
class ImageMinSizeValidator(HelpTextValidatorMixin):
    error_messages = {
        'min_width': _('`%(name)s` is not wide enough. Minimum width is %(width_limit)s pixels.'),
        'min_height': _('`%(name)s` is not tall enough. Minimum height is %(height_limit)s pixels.'),
        'min_size': _('`%(name)s` is too small. Image should be at least %(width_limit)sx%(height_limit)s pixels.'),
    }

    def __init__(self, width: int = 0, height: int = 0):
        self.width_limit = width
        self.height_limit = height

    def __call__(self, file: File):
        closed = file.closed
        try:
            img = Image.open(file)
            image_size = img.size
        except Exception:
            raise ValidationError('`%s` is not an image' % os.path.basename(file.name))
        finally:
            if closed:
                file.close()

        params = {
            'width_limit': self.width_limit,
            'height_limit': self.height_limit,
            'size': image_size,
            'name': file.name
        }

        invalid_width = self.width_limit and image_size[0] < self.width_limit
        invalid_height = self.height_limit and image_size[1] < self.height_limit
        if invalid_width:
            if invalid_height:
                code = 'min_size'
            else:
                code = 'min_width'
        elif invalid_height:
            code = 'min_height'
        else:
            return

        raise ValidationError(self.error_messages[code], code=code, params=params)

    def get_help_text(self):
        if self.width_limit:
            if self.height_limit:
                return _('Minimum image size: {}x{}'.format(self.width_limit, self.height_limit))
            else:
                return _('Minimum image width: {} pixels'.format(self.width_limit))
        elif self.height_limit:
            return _('Minimum image height: {} pixels'.format(self.height_limit))


@deconstructible
class ImageMaxSizeValidator(HelpTextValidatorMixin):
    error_messages = {
        'max_width': _('`%(name)s` is too wide. Maximum width is %(width_limit)s pixels.'),
        'max_height': _('`%(name)s` is too tall. Maximum height is %(height_limit)s pixels.'),
        'max_size': _('`%(name)s` is too big. Image should be at most %(width_limit)sx%(height_limit)s pixels.'),
    }

    def __init__(self, width: int = 0, height: int = 0):
        self.width_limit = width
        self.height_limit = height

    def __call__(self, file: File):
        closed = file.closed
        try:
            img = Image.open(file)
            image_size = img.size
        finally:
            if closed:
                file.close()

        params = {
            'width_limit': self.width_limit,
            'height_limit': self.height_limit,
            'size': image_size,
            'name': file.name
        }

        invalid_width = self.width_limit and image_size[0] > self.width_limit
        invalid_height = self.height_limit and image_size[1] > self.height_limit
        if invalid_width:
            if invalid_height:
                code = 'max_size'
            else:
                code = 'max_width'
        elif invalid_height:
            code = 'max_height'
        else:
            return

        raise ValidationError(self.error_messages[code], code=code, params=params)

    def get_help_text(self):
        if self.width_limit:
            if self.height_limit:
                return _('Maximum image size: {}x{}'.format(self.width_limit, self.height_limit))
            else:
                return _('Maximum image width: {} pixels'.format(self.width_limit))
        elif self.height_limit:
            return _('Maximum image height: {} pixels'.format(self.height_limit))
