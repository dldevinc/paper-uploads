from typing import Dict, Any
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from cloudinary.models import CloudinaryField
from ...models.base import UploadedFileBase, SlaveModelMixin
from .base import CloudinaryFieldMixin


class CloudinaryFile(CloudinaryFieldMixin, SlaveModelMixin, UploadedFileBase):
    file = CloudinaryField(_('file'), resource_type='raw')
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(UploadedFileBase.Meta):
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.display_name,
            'file_info': '({ext}, {size})'.format(
                ext=self.extension,
                size=filesizeformat(self.size)
            ),
        }
