from typing import Any, Dict, Optional

from cloudinary.models import CloudinaryField
from django.utils.translation import gettext_lazy as _

from ...conf import settings
from ...models.base import FileFieldResource, ImageFileResourceMixin
from ...models.mixins import BacklinkModelMixin
from ...utils import filesizeformat
from .base import CloudinaryFieldFile, CloudinaryFileFieldResourceMixin


class CloudinaryImage(ImageFileResourceMixin, BacklinkModelMixin, CloudinaryFileFieldResourceMixin, FileFieldResource):
    file = CloudinaryField(
        _("file"),
        type=settings.CLOUDINARY_TYPE,
        resource_type="image",
    )

    class Meta(FileFieldResource.Meta):
        verbose_name = _("image")
        verbose_name_plural = _("images")

    def get_file(self) -> Optional[CloudinaryFieldFile]:
        if not self.file:
            return None
        return CloudinaryFieldFile(self.file, checksum=self.checksum)

    def get_file_folder(self) -> str:
        owner_field = self.get_owner_field()
        return getattr(owner_field, "upload_to", "") or settings.IMAGES_UPLOAD_TO

    def get_file_field(self) -> CloudinaryField:
        return self._meta.get_field("file")

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "file_info": "({ext}, {width}x{height}, {size})".format(
                ext=self.extension,
                width=self.width,
                height=self.height,
                size=filesizeformat(self.size),
            ),
        }

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
