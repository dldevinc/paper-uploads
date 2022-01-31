from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.cloudinary.models import *
from paper_uploads.models import *
from paper_uploads.validators import *

from .custom import (
    CustomCloudinaryFile,
    CustomCloudinaryGallery,
)

__all__ = [
    "CloudinaryFileExample",
    "CloudinaryImageExample",
    "CloudinaryMediaExample",
    "CloudinaryCollectionFieldObject",
]


class CloudinaryFileExample(models.Model):
    name = models.CharField(_("name"), max_length=128)

    file = CloudinaryFileField(_("file"), blank=True)
    file_required = CloudinaryFileField(_("required file"))
    file_custom = CloudinaryFileField(
        _("custom file"),
        to=CustomCloudinaryFile,
        blank=True,
    )

    file_extensions = CloudinaryFileField(
        _("Extension"),
        blank=True,
        validators=[
            ExtensionValidator([".pdf", ".txt", ".doc"])
        ],
        help_text=_("Only `pdf`, `txt` and `doc` allowed")
    )
    file_mimetypes = CloudinaryFileField(
        _("MimeType"),
        blank=True,
        validators=[
            MimeTypeValidator(["image/svg+xml", "image/gif"])
        ],
        help_text=_("Only `image/svg+xml` and `image/gif` allowed")
    )
    file_size = CloudinaryFileField(
        _("Size"),
        blank=True,
        validators=[
            SizeValidator("16kb")
        ],
        help_text=_("Maximum file size is 16Kb")
    )

    class Meta:
        verbose_name = _("Cloudinary File")
        verbose_name_plural = _("Cloudinary Files")

    def __str__(self):
        return self.name


class CloudinaryImageExample(models.Model):
    image = CloudinaryImageField(_("image"))
    image_public = CloudinaryImageField(
        _("Public image"),
        blank=True,
        cloudinary={
            "type": "upload",
            "folder": "page/images/%Y-%m-%d",
        }
    )

    class Meta:
        verbose_name = _("Cloudinary Image")
        verbose_name_plural = _("Cloudinary Images")

    def __str__(self):
        if self.image:
            return self.image.name
        else:
            return "ImageObject"


class CloudinaryMediaExample(models.Model):
    media = CloudinaryMediaField(_("media"))

    class Meta:
        verbose_name = _("Cloudinary Media")
        verbose_name_plural = _("Cloudinary Media")

    def __str__(self):
        if self.media:
            return self.media.name
        else:
            return "MediaObject"


class CloudinaryFileCollection(Collection):
    file = CollectionItem(CloudinaryFileItem)


class CloudinaryPhotoCollection(CloudinaryImageCollection):
    pass


class CloudinaryMediaCollection(Collection):
    media = CollectionItem(CloudinaryMediaItem)


class CloudinaryCompleteCollection(Collection):
    image = CollectionItem(CloudinaryImageItem)
    media = CollectionItem(CloudinaryMediaItem)
    file = CollectionItem(CloudinaryFileItem)


class CloudinaryCollectionFieldObject(models.Model):
    file_collection = CollectionField(CloudinaryFileCollection)
    image_collection = CollectionField(CloudinaryPhotoCollection)
    media_collection = CollectionField(CloudinaryMediaCollection)
    full_collection = CollectionField(CloudinaryCompleteCollection)
    custom_collection = CollectionField(CustomCloudinaryGallery)

    class Meta:
        verbose_name = _("Cloudinary Collection")
        verbose_name_plural = _("Cloudinary Collections")

    def __str__(self):
        return "CloudinaryCollectionObject"
