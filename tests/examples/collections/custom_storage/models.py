from django.db import models
from django.utils.translation import gettext_lazy as _
from storages.backends.dropbox import DropBoxStorage

from paper_uploads.models import *


class MixedCollection(Collection):
    svg = CollectionItem(SVGItem, options={
        "storage": DropBoxStorage(),
        "upload_to": "collection/svg",
    })
    image = CollectionItem(ImageItem, options={
        "storage": DropBoxStorage(),
        "upload_to": "collection/images",
    })
    file = CollectionItem(FileItem, options={
        "storage": DropBoxStorage(),
        "upload_to": "collection/files",
    })


class Photos(ImageCollection):
    image = CollectionItem(ImageItem, options={
        "storage": DropBoxStorage(),
        "upload_to": "gallery",
        "variations": dict(
            desktop=dict(
                size=(800, 0),
                clip=False,
            ),
        )
    })


class Page(models.Model):
    collection = CollectionField(
        MixedCollection,
        verbose_name=_("collection")
    )
    gallery = CollectionField(
        Photos,
        verbose_name=_("gallery")
    )

    class Meta:
        verbose_name = _("Page")
