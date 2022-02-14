from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *
from paper_uploads.cloudinary.models import *


class FilesOnlyCollection(Collection):
    file = CollectionItem(CloudinaryFileItem)


class ImagesOnlyCollection(CloudinaryImageCollection):
    pass


class MixedCollection(Collection):
    image = CollectionItem(CloudinaryImageItem)
    media = CollectionItem(CloudinaryMediaItem)
    file = CollectionItem(CloudinaryFileItem)


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
