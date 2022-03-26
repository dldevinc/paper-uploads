from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class Page(models.Model):
    file = FileField(
        _("file"),
        blank=True
    )
    svg = SVGFileField(
        _("svg"),
        blank=True
    )
    image = ImageField(
        _("image"),
        blank=True
    )
    image_group = ImageField(
        _("image group"),
        blank=True,
        variations=dict(
            desktop=dict(
                size=(800, 0),
                clip=False,
            ),
            mobile=dict(
                size=(0, 600),
                clip=False,
                versions={"webp", "2x"},
            ),
        )
    )

    class Meta:
        verbose_name = _("Page")
