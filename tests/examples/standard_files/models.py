from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class Page(models.Model):
    file = FileField(
        _("file"),
        blank=True
    )
    image = ImageField(
        _("image"),
        blank=True
    )

    class Meta:
        verbose_name = _("Page")
