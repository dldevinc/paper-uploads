from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *

__all__ = [
    "FileExample",
    "ImageExample",
]


class FileExample(models.Model):
    file = FileField(_("file"))


class ImageExample(models.Model):
    image = ImageField(_("image"), variations=dict(
        desktop=dict(
            size=(800, 0),
            clip=False
        ),
        mobile=dict(
            size=(0, 600),
            clip=False
        ),
    ))
