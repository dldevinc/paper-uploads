from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *
from paper_uploads.validators import (
    ImageMaxSizeValidator,
    ImageMinSizeValidator,
    MimeTypeValidator,
    MaxSizeValidator,
)


class Gallery(ImageCollection):
    VALIDATORS = [
        ImageMinSizeValidator(640, 480),
        ImageMaxSizeValidator(4000, 3000)
    ]


class MixedCollection(Collection):
    svg = CollectionItem(SVGItem, validators=[
        MimeTypeValidator(["image/svg+xml"])
    ])
    image = CollectionItem(ImageItem, validators=[
        ImageMinSizeValidator(640, 480),
        ImageMaxSizeValidator(4000, 3000)
    ])
    file = CollectionItem(FileItem, validators=[
        MaxSizeValidator("1Mb")
    ])


class Page(models.Model):
    gallery = CollectionField(
        Gallery,
        verbose_name=_("gallery")
    )
    collection = CollectionField(
        MixedCollection,
        verbose_name=_("mixed collection")
    )

    class Meta:
        verbose_name = _("Page")
