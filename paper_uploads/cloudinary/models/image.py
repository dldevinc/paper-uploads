from typing import Dict, Any
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from cloudinary.models import CloudinaryField
from ...models.base import UploadedFileBase, SlaveModelMixin
from ...models.image import UploadedImageBase
from .base import CloudinaryFieldMixin


class CloudinaryImage(CloudinaryFieldMixin, SlaveModelMixin, UploadedImageBase):
    cloudinary_resource_type = 'image'

    file = CloudinaryField(_('file'), resource_type='image')

    class Meta(UploadedFileBase.Meta):
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def _post_attach_file(self, data=None):
        super()._post_attach_file(data)
        if isinstance(data, dict):
            if 'width' in data:
                self.width = data['width']
            if 'height' in data:
                self.height = data['height']

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
