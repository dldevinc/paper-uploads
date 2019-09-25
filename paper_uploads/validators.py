from PIL import Image
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat


@deconstructible
class SizeLimitValidator:
    message = _('Ensure that the size of the file is not more than %(show_limit_value)s.')
    code = 'size_limit'

    def __init__(self, limit_value, message=None):
        self.limit_value = limit_value
        if message:
            self.message = message

    def __call__(self, value):
        params = {
            'limit_value': self.limit_value,
            'show_limit_value': filesizeformat(self.limit_value),
            'value': value.size
        }
        if value.size > self.limit_value:
            raise ValidationError(self.message, code=self.code, params=params)


@deconstructible
class ImageMinSizeValidator:
    error_messages = {
        'min_width': _('Image should be at least %(width_limit)s pixels wide.'),
        'min_height': _('Image should be at least %(height_limit)s pixels tall.'),
        'min_size': _('Image should be at least %(width_limit)s x %(height_limit)s pixels.'),
    }

    def __init__(self, width=0, height=0):
        self.width_limit = width
        self.height_limit = height

    def __call__(self, value):
        closed = value.closed
        try:
            img = Image.open(value)
            image_size = img.size
        finally:
            if closed:
                value.close()

        params = {
            'width_limit': self.width_limit,
            'height_limit': self.height_limit,
            'value': image_size
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


@deconstructible
class ImageMaxSizeValidator:
    error_messages = {
        'max_width': _('Image should be at most %(width_limit)s pixels wide.'),
        'max_height': _('Image should be at most %(height_limit)s pixels tall.'),
        'max_size': _('Image should be at most %(width_limit)s x %(height_limit)s pixels.'),
    }

    def __init__(self, width=0, height=0):
        self.width_limit = width
        self.height_limit = height

    def __call__(self, value):
        closed = value.closed
        try:
            img = Image.open(value)
            image_size = img.size
        finally:
            if closed:
                value.close()

        params = {
            'width_limit': self.width_limit,
            'height_limit': self.height_limit,
            'value': image_size
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
