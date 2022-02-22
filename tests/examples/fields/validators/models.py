from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *
from paper_uploads.validators import (
    ExtensionValidator,
    ImageMaxSizeValidator,
    ImageMinSizeValidator,
    MimeTypeValidator,
    MaxSizeValidator,
)


class Page(models.Model):
    filter_ext = FileField(
        _("extension"),
        blank=True,
        validators=[
            ExtensionValidator([".pdf", ".txt", ".doc"])
        ],
        help_text=_("Only `pdf`, `txt` and `doc` allowed")
    )
    filter_mime = FileField(
        _("MIME type"),
        blank=True,
        validators=[
            MimeTypeValidator(["image/svg+xml", "image/gif"])
        ],
        help_text=_("Only `image/svg+xml` and `image/gif` allowed")
    )
    filter_size = FileField(
        _("size"),
        blank=True,
        validators=[
            MaxSizeValidator("16kb")
        ],
        help_text=_("Maximum file size is 16Kb")
    )
    filter_min_size = ImageField(
        _("minimum size"),
        blank=True,
        validators=[
            ImageMinSizeValidator(640, 480)
        ],
        help_text=_("Image should be at least 640x480 pixels")
    )
    filter_max_size = ImageField(
        _("maximum size"),
        blank=True,
        validators=[
            ImageMaxSizeValidator(1024, 768)
        ],
        help_text=_("Image should be at most 1024x768 pixels")
    )

    filter_image_ext = ImageField(
        _("extension (image)"),
        blank=True,
        validators=[
            ExtensionValidator([".gif", ".png"])
        ],
        help_text=_("Only `png` and `gif` allowed")
    )

    class Meta:
        verbose_name = _("Page")
