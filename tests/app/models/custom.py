from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.cloudinary.models import *
from paper_uploads.models import *

__all__ = [
    "CustomCloudinaryFile",
    "CustomCloudinaryGallery",
]


class CustomCloudinaryFile(CloudinaryFile):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "custom-files/%Y"


class CustomCloudinaryImageItem(CloudinaryImageItemBase):
    caption = models.TextField(_("caption"), blank=True)

    def get_file_folder(self) -> str:
        return "collections/custom-images/%Y"


class CustomCloudinaryGallery(CloudinaryImageCollection):
    image = CollectionItem(CustomCloudinaryImageItem)
