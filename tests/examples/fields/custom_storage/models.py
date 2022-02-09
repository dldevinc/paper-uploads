from django.db import models
from django.utils.translation import gettext_lazy as _
from storages.backends.dropbox import DropBoxStorage

from paper_uploads.models import *


class Page(models.Model):
    file = FileField(
        _("file"),
        blank=True,
        storage=DropBoxStorage(),
        upload_to="files"
    )
    image = ImageField(
        _("image"),
        blank=True,
        storage=DropBoxStorage(),
        upload_to="images",
        variations=dict(
            small=dict(
                size=(600, 0),
                clip=False
            )
        )
    )

    class Meta:
        verbose_name = _("Page")
