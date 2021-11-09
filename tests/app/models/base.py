from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *

__all__ = [
    "FileExample",
    "ImageExample",
    "FileCollection",
    "PhotoCollection",
    "CompleteCollection",
    "IsolatedFileCollection",
    "ChildFileCollection",
]


class FileExample(models.Model):
    file = FileField(_("file"))


class ImageExample(models.Model):
    image = ImageField(_("image"), variations=dict(
        desktop=dict(
            size=(800, 0),
            clip=False
        ),
        mobile=dict(
            size=(0, 600),
            clip=False
        ),
    ))


class FileCollection(Collection):
    file = CollectionItem(FileItem)


class PhotoCollection(ImageCollection):
    pass


class IsolatedFileCollection(Collection):
    file = CollectionItem(FileItem)
    name = models.CharField(_("name"), max_length=128, blank=True)

    class Meta:
        proxy = False


class ChildFileCollection(IsolatedFileCollection):
    file = None
    image = CollectionItem(ImageItem)
    svg = CollectionItem(SVGItem)


class CompleteCollection(Collection):
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)

    VARIATIONS = dict(
        desktop=dict(
            size=(800, 0),
            clip=False
        ),
        mobile=dict(
            size=(0, 600),
            clip=False
        ),
    )
