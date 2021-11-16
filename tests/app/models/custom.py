from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.cloudinary.models import *
from paper_uploads.models import *

__all__ = [
    "CustomProxyUploadedFile",
    "CustomProxyUploadedImage",
    "CustomProxyGallery",
    "CustomGallery",
    "CustomImageItem",
    "CustomCloudinaryFile",
    "CustomCloudinaryGallery",
]


# =========== Proxy models ==================


class CustomProxyUploadedFile(UploadedFile):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "custom-files/%Y"


class CustomProxyUploadedImage(UploadedImage):
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
    change_form_class = "app.forms.dialogs.custom.CustomImageItemDialog"

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
