import posixpath
from typing import Dict, Any
from django.db import models
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from cloudinary.models import CloudinaryField
from ...models.base import UploadedFileBase, SlaveModelMixin
from ..container import CloudinaryContainerMixin


class CloudinaryMedia(CloudinaryContainerMixin, SlaveModelMixin, UploadedFileBase):
    cloudinary_resource_type = 'video'

    file = CloudinaryField(_('file'), resource_type='video')
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(UploadedFileBase.Meta):
        verbose_name = _('media')
        verbose_name_plural = _('media')

    def attach_file(self, file: File, **options):
        # set name without Cloudinary suffix
        basename = posixpath.basename(file.name)
        file_name, file_ext = posixpath.splitext(basename)
        self.name = file_name
        super().attach_file(file, **options)

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    @classmethod
    def get_validation(cls) -> Dict[str, Any]:
        return {
            **super().get_validation(),
            'acceptFiles': ['.3gp', '.avi', '.flv', '.mkv', '.mov', '.wmv', '.aac', '.wma', 'video/*', 'audio/*'],
        }

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.display_name,
            'file_info': '({ext}, {size})'.format(
                ext=self.extension,
                size=filesizeformat(self.size)
            ),
        }
