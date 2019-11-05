from typing import Dict, Any, Union, IO
from django.db import models
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from ...models.base import ReverseFieldModelMixin
from .base import CloudinaryFileResource, ReadonlyCloudinaryFileProxyMixin


class CloudinaryFile(ReverseFieldModelMixin, ReadonlyCloudinaryFileProxyMixin, CloudinaryFileResource):
    cloudinary_resource_type = 'raw'

    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(CloudinaryFileResource.Meta):
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def attach_file(self, file: Union[File, IO], name: str = None, **options):
        """
        Установка опций загрузки файла из параметров поля
        """
        owner_field = self.get_owner_field()
        if owner_field is not None and hasattr(owner_field, 'cloudinary_options'):
            options.setdefault('cloudinary', owner_field.cloudinary_options)
        return super().attach_file(file, name, **options)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.display_name,
            'file_info': '({ext}, {size})'.format(
                ext=self.extension,
                size=filesizeformat(self.size)
            ),
        }
