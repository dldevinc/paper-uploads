from typing import Any, Dict

from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.cloudinary.models import *
from paper_uploads.models import *
from paper_uploads.validators import *

from .base import CompleteCollection, FileCollection, PhotoCollection

__all__ = [
    "CustomImageItem",
    "CustomGallery",

    "FileFieldObject",
    "ImageFieldObject",
    "CollectionFieldObject",

    "CloudinaryFileExample",
    "CloudinaryImageExample",
    "CloudinaryMediaExample",
    "CloudinaryCollectionFieldObject",
]


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


class CustomImageItem(ImageItemBase):
    caption = models.TextField(_("caption"), blank=True)


class CustomGallery(Collection):
    VARIATIONS = dict(
        desktop=dict(
            size=(1200, 0),
            clip=False,
        )
    )

    image = CollectionItem(CustomProxyImageItem)
    custom_image = CollectionItem(CustomImageItem)

    @classmethod
    def get_configuration(cls) -> Dict[str, Any]:
        return {
            "strictImageValidation": True,
            "acceptFiles": [
                "image/*",
            ],
        }


class CustomCloudinaryFile(CloudinaryFile):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "custom-files/%Y"


# ======================================================================================


class FileFieldObject(models.Model):
    name = models.CharField(_("name"), max_length=128)

    file = FileField(_("file"), blank=True)
    file_required = FileField(_("required file"))
    file_custom = FileField(
        _("custom file"),
        to=CustomUploadedFile,
        blank=True,
    )

    file_extensions = FileField(
        _("Extension"),
        blank=True,
        validators=[
            ExtensionValidator([".pdf", ".txt", ".doc"])
        ],
        help_text=_("Only `pdf`, `txt` and `doc` allowed")
    )
    file_mimetypes = FileField(
        _("MimeType"),
        blank=True,
        validators=[
            MimeTypeValidator(["image/svg+xml", "image/gif"])
        ],
        help_text=_("Only `image/svg+xml` and `image/gif` allowed")
    )
    file_size = FileField(
        _("Size"),
        blank=True,
        validators=[
            SizeValidator("16kb")
        ],
        help_text=_("Maximum file size is 16Kb")
    )

    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")

    def __str__(self):
        return self.name


class ImageFieldObject(models.Model):
    name = models.CharField(_("name"), max_length=128)

    image = ImageField(_("image"), blank=True)
    image_required = ImageField(
        _("required image"),
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
    image_custom = ImageField(
        _("custom image"),
        to=CustomUploadedImage,
        blank=True,
    )

    image_extensions = ImageField(
        _("Extension"),
        blank=True,
        validators=[
            ExtensionValidator([".png", ".gif"])
        ],
        help_text=_("Only `png` and `gif` allowed")
    )
    image_mimetypes = ImageField(
        _("MimeType"),
        blank=True,
        validators=[
            MimeTypeValidator(["image/png", "image/jpeg"])
        ],
        help_text=_("Only `image/png` and `image/jpeg` allowed")
    )
    image_size = ImageField(
        _("Size"),
        blank=True,
        validators=[
            SizeValidator("64kb")
        ],
        help_text=_("Maximum file size is 64Kb")
    )
    image_min_size = ImageField(
        _("Min size"),
        blank=True,
        validators=[
            ImageMinSizeValidator(640, 480)
        ],
        help_text=_("Image should be at least 640x480 pixels")
    )
    image_max_size = ImageField(
        _("Max size"),
        blank=True,
        validators=[
            ImageMaxSizeValidator(1024, 768)
        ],
        help_text=_("Image should be at most 1024x768 pixels")
    )

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")

    def __str__(self):
        return self.name


class CollectionFieldObject(models.Model):
    name = models.CharField(_("name"), max_length=128)

    file_collection = CollectionField(FileCollection)
    image_collection = CollectionField(PhotoCollection)
    full_collection = CollectionField(CompleteCollection)
    custom_collection = CollectionField(CustomGallery)

    class Meta:
        verbose_name = _("Collection")
        verbose_name_plural = _("Collections")

    def __str__(self):
        return self.name


# ======================================================================================


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

    class Meta:
        verbose_name = _("Cloudinary Collection")
        verbose_name_plural = _("Cloudinary Collections")

    def __str__(self):
        return "CloudinaryCollectionObject"
