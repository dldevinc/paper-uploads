import posixpath
from typing import Dict, Any
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from cloudinary.models import CloudinaryField
from ...models.base import UploadedFileBase, SlaveModelMixin, ProxyFileAttributesMixin
from ...models.image import UploadedImageBase
from ..container import CloudinaryContainerMixin


class CloudinaryImage(CloudinaryContainerMixin, ProxyFileAttributesMixin, SlaveModelMixin, UploadedImageBase):
    cloudinary_resource_type = 'image'

    file = CloudinaryField(_('file'), resource_type='raw')

    class Meta(UploadedFileBase.Meta):
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def attach_file(self, file: File):
        # set name without Cloudinary suffix
        basename = posixpath.basename(file.name)
        file_name, file_ext = posixpath.splitext(basename)
        self.name = file_name
        super(UploadedImageBase, self).attach_file(file)

    @classmethod
    def get_validation(cls) -> Dict[str, Any]:
        return {
            **super().get_validation(),
            'acceptFiles': ['image/*'],
        }

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'width': self.width,
            'height': self.height,
            'file_info': '({ext}, {width}x{height}, {size})'.format(
                ext=self.extension,
                width=self.width,
                height=self.height,
                size=filesizeformat(self.size)
            )
        }
