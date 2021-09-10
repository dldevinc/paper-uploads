from typing import Any, Dict, Optional

from cloudinary.models import CloudinaryField
from django.db import models
from django.utils.translation import gettext_lazy as _

from ...conf import settings
from ...utils import filesizeformat
from .base import CloudinaryFieldFile, CloudinaryFileResource


class CloudinaryFile(CloudinaryFileResource):
    file = CloudinaryField(
        _("file"),
        type=settings.CLOUDINARY_TYPE,
        resource_type="raw",
    )
    display_name = models.CharField(_("display name"), max_length=255, blank=True)

    class Meta(CloudinaryFileResource.Meta):
        verbose_name = _("file")
        verbose_name_plural = _("files")

    def get_file_folder(self) -> str:
        return settings.FILES_UPLOAD_TO

    def get_file(self) -> Optional[CloudinaryFieldFile]:
        if not self.file:
            return None
        return CloudinaryFieldFile(self.file, checksum=self.checksum)

    def set_file(self, value):
        self.file = value

    def get_file_field(self) -> CloudinaryField:
        return self._meta.get_field("file")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.basename
        super().save(*args, **kwargs)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.display_name,
            "file_info": "({ext}, {size})".format(
                ext=self.extension, size=filesizeformat(self.size)
            ),
        }
