from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class PhotoCollection(ImageCollection):
    VARIATIONS = dict(
        desktop=dict(
            size=(800, 0),
            clip=False
        ),
        mobile=dict(
            size=(0, 600),
            clip=False
        ),
        admin_preview=dict(
            size=(200, 100),
            versions={"webp", "2x"},
        )
    )


class Page(models.Model):
    image = ImageField(
        _("image"),
        blank=True,
        variations=dict(
            desktop=dict(
                name="desktop",
                size=(800, 0),
                clip=False
            ),
            mobile=dict(
                name="mobile",
                size=(0, 600),
                clip=False
            ),
        )
    )
    collection = CollectionField(
        PhotoCollection,
        verbose_name=_("collection")
    )

    class Meta:
        verbose_name = _("Page")
