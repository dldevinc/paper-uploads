from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class FilesOnlyCollection(Collection):
    file = CollectionItem(FileItem)


class ImagesOnlyCollection(ImageCollection):
    VARIATIONS = dict(
        desktop=dict(
            size=(800, 0),
            clip=False,
        ),
        mobile=dict(
            size=(0, 600),
            clip=False,
        ),
    )


class MixedCollection(Collection):
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)


class Page(models.Model):
    file_collection = CollectionField(
        FilesOnlyCollection,
        verbose_name=_("file collection")
    )
    image_collection = CollectionField(
        ImagesOnlyCollection,
        verbose_name=_("image collection")
    )
    mixed_collection = CollectionField(
        MixedCollection,
        verbose_name=_("mixed collection")
    )

    class Meta:
        verbose_name = _("Page")
