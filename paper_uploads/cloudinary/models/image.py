from typing import IO, Any, Dict, Union

from django.core.files import File
from django.dispatch import receiver
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from ... import signals
from ...conf import settings
from ...models.base import ImageFileResourceMixin, ReverseFieldModelMixin
from .base import CloudinaryFileResource, ReadonlyCloudinaryFileProxyMixin


class CloudinaryImage(
    ReverseFieldModelMixin,
    ReadonlyCloudinaryFileProxyMixin,
    ImageFileResourceMixin,
    CloudinaryFileResource,
):
    cloudinary_resource_type = 'image'

    class Meta(CloudinaryFileResource.Meta):
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def attach_file(self, file: Union[File, IO], name: str = None, **options):
        """
        Установка опций загрузки файла из параметров поля
        """
        cloudinary_options = settings.CLOUDINARY.copy()
        owner_field = self.get_owner_field()
        if owner_field is not None and hasattr(owner_field, 'cloudinary_options'):
            cloudinary_options.update(owner_field.cloudinary_options or {})
        options.setdefault('cloudinary', cloudinary_options)
        return super().attach_file(file, name, **options)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'file_info': '({ext}, {width}x{height}, {size})'.format(
                ext=self.extension,
                width=self.width,
                height=self.height,
                size=filesizeformat(self.size),
            ),
        }

    @classmethod
    def get_validation(cls) -> Dict[str, Any]:
        # TODO: магический метод
        return {
            'acceptFiles': ['image/*'],
        }


@receiver(signals.post_attach_file)
def on_attach(sender, **kwargs):
    instance = kwargs['instance']
    response = kwargs['response']
    if isinstance(response, dict):
        if 'width' in response:
            instance.width = response['width']
        if 'height' in response:
            instance.height = response['height']
