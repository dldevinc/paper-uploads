from typing import Any, Dict, Optional

from cloudinary.models import CloudinaryField
from django.db import models
from django.utils.translation import gettext_lazy as _

from ...conf import settings
from ...models.base import FileFieldResource
from ...models.mixins import BacklinkModelMixin
from ...utils import filesizeformat
from .base import CloudinaryFieldFile, CloudinaryFileFieldResourceMixin


class CloudinaryFile(BacklinkModelMixin, CloudinaryFileFieldResourceMixin, FileFieldResource):
    file = CloudinaryField(
        _("file"),
        type=settings.CLOUDINARY_TYPE,
        resource_type="raw",
    )
    display_name = models.CharField(_("display name"), max_length=255, blank=True)

    class Meta(FileFieldResource.Meta):
        verbose_name = _("file")
        verbose_name_plural = _("files")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.resource_name
        super().save(*args, **kwargs)

    def get_file(self) -> Optional[CloudinaryFieldFile]:
        if not self.file:
            return None
        return CloudinaryFieldFile(self.file, checksum=self.checksum)

    def get_file_folder(self) -> str:
        owner_field = self.get_owner_field()
        return getattr(owner_field, "upload_to", "") or settings.FILES_UPLOAD_TO

    def get_file_field(self) -> CloudinaryField:
        return self._meta.get_field("file")

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.display_name or self.resource_name,
            "file_info": "({ext}, {size})".format(
                ext=self.extension, size=filesizeformat(self.size)
            ),
        }
