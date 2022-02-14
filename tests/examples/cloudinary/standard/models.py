from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.cloudinary.models import *


class Page(models.Model):
    file = CloudinaryFileField(
        _("file"),
        blank=True
    )
    image = CloudinaryImageField(
        _("image"),
        blank=True
    )
    media = CloudinaryMediaField(
        _("media"),
        blank=True
    )

    class Meta:
        verbose_name = _("Page")
