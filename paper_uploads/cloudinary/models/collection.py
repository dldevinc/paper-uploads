from typing import Any, Dict, Optional

import magic
from cloudinary.models import CloudinaryField
from django.core.files import File
from django.db import models
from django.utils.translation import gettext_lazy as _

from ...conf import IMAGE_ITEM_VARIATIONS, settings
from ...models.base import FileFieldResource, ImageFileResourceMixin
from ...models.collection import Collection, CollectionFileItemBase, FilePreviewMixin
from ...models.fields import CollectionItem
from .base import CloudinaryFieldFile, CloudinaryFileFieldResourceMixin

__all__ = [
    "CloudinaryFileItemBase",
    "CloudinaryMediaItemBase",
    "CloudinaryImageItemBase",
    "CloudinaryFileItem",
    "CloudinaryMediaItem",
    "CloudinaryImageItem",
    "CloudinaryImageCollection",
]


class CollectionCloudinaryFileItemBase(CloudinaryFileFieldResourceMixin, CollectionFileItemBase):
    class Meta:
        abstract = True


class CloudinaryFileItemBase(FilePreviewMixin, CollectionCloudinaryFileItemBase):
    change_form_class = "paper_uploads.forms.dialogs.collection.ChangeFileItemDialog"
    template_name = "paper_uploads/items/file.html"
    preview_template_name = "paper_uploads/items/preview/file.html"

    file = CloudinaryField(
        _("file"),
        type=settings.CLOUDINARY_TYPE,
        resource_type="raw",
    )
    display_name = models.CharField(_("display name"), max_length=255, blank=True)

    class Meta(CollectionCloudinaryFileItemBase.Meta):
        abstract = True
        verbose_name = _("File item")
        verbose_name_plural = _("File items")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.resource_name
        super().save(*args, **kwargs)

    def get_file_folder(self) -> str:
        item_type_field = self.get_item_type_field()
        return item_type_field.options.get("upload_to") or settings.COLLECTION_FILES_UPLOAD_TO

    def get_file(self) -> Optional[CloudinaryFieldFile]:
        if not self.file:
            return None
        return CloudinaryFieldFile(self.file, checksum=self.checksum)

    def set_file(self, value):
        self.file = value

    def get_file_field(self) -> CloudinaryField:
        return self._meta.get_field("file")

    def get_caption(self):
        name = self.display_name or self.resource_name
        if self.extension:
            return "{}.{}".format(name, self.extension)
        return name

    @classmethod
    def accept(cls, file: File) -> bool:
        return True


class CloudinaryMediaItemBase(FilePreviewMixin, CollectionCloudinaryFileItemBase):
    change_form_class = "paper_uploads.forms.dialogs.collection.ChangeFileItemDialog"
    template_name = "paper_uploads/items/file.html"
    preview_template_name = "paper_uploads/items/preview/file.html"

    file = CloudinaryField(
        _("file"),
        type=settings.CLOUDINARY_TYPE,
        resource_type="video",
    )
    display_name = models.CharField(_("display name"), max_length=255, blank=True)

    class Meta(CollectionCloudinaryFileItemBase.Meta):
        abstract = True
        verbose_name = _("Media item")
        verbose_name_plural = _("Media items")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.resource_name
        super().save(*args, **kwargs)

    def get_file_folder(self) -> str:
        item_type_field = self.get_item_type_field()
        return item_type_field.options.get("upload_to") or settings.COLLECTION_FILES_UPLOAD_TO

    def get_file(self) -> Optional[CloudinaryFieldFile]:
        if not self.file:
            return None
        return CloudinaryFieldFile(self.file, checksum=self.checksum)

    def set_file(self, value):
        self.file = value

    def get_file_field(self) -> CloudinaryField:
        return self._meta.get_field("file")

    @classmethod
    def accept(cls, file: File) -> bool:
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # correct file position after mimetype detection
        basetype, subtype = mimetype.split("/", 1)
        return basetype in {"video", "audio"}


class CloudinaryImageItemBase(ImageFileResourceMixin, CollectionCloudinaryFileItemBase):
    PREVIEW_VARIATIONS = IMAGE_ITEM_VARIATIONS
    change_form_class = "paper_uploads.forms.dialogs.collection.ChangeImageItemDialog"
    template_name = "paper_uploads_cloudinary/items/image.html"
    preview_template_name = "paper_uploads_cloudinary/items/preview/image.html"

    file = CloudinaryField(
        _("file"),
        type=settings.CLOUDINARY_TYPE,
        resource_type="image",
    )

    class Meta(CollectionCloudinaryFileItemBase.Meta):
        abstract = True
        verbose_name = _("Image item")
        verbose_name_plural = _("Image items")

    def get_file_folder(self) -> str:
        item_type_field = self.get_item_type_field()
        return item_type_field.options.get("upload_to") or settings.COLLECTION_IMAGES_UPLOAD_TO

    def get_file(self) -> Optional[CloudinaryFieldFile]:
        if not self.file:
            return None
        return CloudinaryFieldFile(self.file, checksum=self.checksum)

    def set_file(self, value):
        self.file = value

    def get_file_field(self) -> CloudinaryField:
        return self._meta.get_field("file")

    @classmethod
    def accept(cls, file: File) -> bool:
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # correct file position after mimetype detection
        basetype, subtype = mimetype.split("/", 1)
        return basetype == "image"


class CloudinaryFileItem(CloudinaryFileItemBase):
    pass


class CloudinaryMediaItem(CloudinaryMediaItemBase):
    pass


class CloudinaryImageItem(CloudinaryImageItemBase):
    pass


# ==============================================================================


class CloudinaryImageCollection(Collection):
    image = CollectionItem(CloudinaryImageItem)

    @classmethod
    def get_configuration(cls) -> Dict[str, Any]:
        return {
            "strictImageValidation": True,
            "acceptFiles": [
                "image/bmp",
                "image/gif",
                "image/jpeg",
                "image/png",
                # "image/svg+xml",
                "image/tiff",
                "image/webp",
            ],
        }
