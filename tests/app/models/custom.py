from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *
from paper_uploads.cloudinary.models import *

__all__ = [
    "CustomUploadedFile",
    "CustomUploadedImage",
    "CustomCloudinaryFile",
    "CustomProxyGallery",
    "CustomGallery",
    "CustomCloudinaryGallery",
]


# =========== Proxy models ==================


class CustomUploadedFile(UploadedFile):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "custom-files/%Y"


class CustomUploadedImage(UploadedImage):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "custom-images/%Y"


class CustomProxyImageItem(ImageItem):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "collections/custom-images/%Y"


class CustomCloudinaryFile(CloudinaryFile):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "custom-files/%Y"


# =========== Concrete models ==================


class CustomImageItem(ImageItemBase):
    caption = models.TextField(_("caption"), blank=True)

    def get_file_folder(self) -> str:
        return "collections/custom-images/%Y"


class CustomCloudinaryImageItem(CloudinaryImageItemBase):
    caption = models.TextField(_("caption"), blank=True)

    def get_file_folder(self) -> str:
        return "collections/custom-images/%Y"


class CustomProxyGallery(ImageCollection):
    VARIATIONS = dict(
        desktop=dict(
            size=(1200, 0),
            clip=False,
        )
    )

    image = CollectionItem(CustomProxyImageItem)


class CustomGallery(ImageCollection):
    VARIATIONS = dict(
        desktop=dict(
            size=(1200, 0),
            clip=False,
        )
    )

    image = CollectionItem(CustomImageItem)


class CustomCloudinaryGallery(CloudinaryImageCollection):
    image = CollectionItem(CustomCloudinaryImageItem)
