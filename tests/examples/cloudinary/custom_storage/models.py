from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.cloudinary.models import *


class Page(models.Model):
    file = CloudinaryFileField(
        _("file"),
        blank=True,
        upload_to="custom-files/%Y",
    )
    image = CloudinaryImageField(
        _("image"),
        blank=True,
        upload_to="custom-images/%Y"
    )
    media = CloudinaryMediaField(
        _("media"),
        blank=True,
        upload_to="custom-media/%Y"
    )

    class Meta:
        verbose_name = _("Page")
