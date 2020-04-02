from typing import IO, Any, Dict, Optional, Union

import magic
from django.core.files import File
from django.db import models
from django.template import loader
from django.utils.translation import gettext_lazy as _

from ...conf import settings
from ...models.base import ImageFileResourceMixin
from ...models.collection import (
    Collection,
    CollectionResourceItem,
    FilePreviewItemMixin,
)
from ...models.fields import ItemField
from .base import CloudinaryFileResource, ReadonlyCloudinaryFileProxyMixin

__all__ = [
    'CloudinaryFileItem',
    'CloudinaryMediaItem',
    'CloudinaryImageItem',
    'CloudinaryCollection',
    'CloudinaryImageCollection',
]


class CollectionCloudinaryFileResource(CollectionResourceItem, CloudinaryFileResource):
    class Meta(CollectionResourceItem.Meta):
        abstract = True

    def attach_file(self, file: Union[File, IO], name: str = None, **options):
        """
        Установка опций загрузки файла из параметров поля
        """
        cloudinary_options = settings.CLOUDINARY.copy()
        itemtype_field = self.get_itemtype_field()
        if itemtype_field is not None and 'cloudinary' in itemtype_field.options:
            cloudinary_options.update(itemtype_field.options['cloudinary'])
        options.setdefault('cloudinary', cloudinary_options)
        return super().attach_file(file, name, **options)

    @property
    def caption(self):
        return self.get_basename()


class CloudinaryFileItem(
    FilePreviewItemMixin,
    ReadonlyCloudinaryFileProxyMixin,
    CollectionCloudinaryFileResource,
):
    change_form_class = 'paper_uploads.forms.dialogs.collection.FileItemDialog'
    admin_template_name = 'paper_uploads/collection_item/file.html'

    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(CollectionCloudinaryFileResource.Meta):
        verbose_name = _('File item')
        verbose_name_plural = _('File items')

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.display_name,
        }

    @classmethod
    def file_supported(cls, file: File) -> bool:
        # TODO: магический метод
        return True


class CloudinaryMediaItem(
    FilePreviewItemMixin,
    ReadonlyCloudinaryFileProxyMixin,
    CollectionCloudinaryFileResource,
):
    change_form_class = 'paper_uploads.forms.dialogs.collection.FileItemDialog'
    admin_template_name = 'paper_uploads/collection_item/file.html'
    cloudinary_resource_type = 'video'

    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(CollectionCloudinaryFileResource.Meta):
        verbose_name = _('Media item')
        verbose_name_plural = _('Media items')

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.display_name,
        }

    @classmethod
    def file_supported(cls, file: File) -> bool:
        # TODO: магический метод
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # correct file position after mimetype detection
        basetype, subtype = mimetype.split('/', 1)
        return basetype in {'video', 'audio'}


class CloudinaryImageItem(
    ReadonlyCloudinaryFileProxyMixin,
    ImageFileResourceMixin,
    CollectionCloudinaryFileResource,
):
    PREVIEW_VARIATIONS = settings.COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS
    change_form_class = 'paper_uploads.forms.dialogs.collection.ImageItemDialog'
    admin_template_name = 'paper_uploads_cloudinary/collection_item/image.html'
    cloudinary_resource_type = 'image'

    class Meta(CollectionCloudinaryFileResource.Meta):
        verbose_name = _('Image item')
        verbose_name_plural = _('Image items')

    @property
    def preview(self):
        return loader.render_to_string(
            'paper_uploads_cloudinary/collection_item/preview/image.html',
            {
                'item': self,
                'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            },
        )

    @classmethod
    def file_supported(cls, file: File) -> bool:
        # TODO: магический метод
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # correct file position after mimetype detection
        basetype, subtype = mimetype.split('/', 1)
        return basetype == 'image'


class CloudinaryCollection(Collection):
    image = ItemField(CloudinaryImageItem)
    media = ItemField(CloudinaryMediaItem)
    file = ItemField(CloudinaryFileItem)


class CloudinaryImageCollection(Collection):
    image = ItemField(CloudinaryImageItem)

    @classmethod
    def get_validation(cls) -> Dict[str, Any]:
        # TODO: магический метод
        return {
            'acceptFiles': ['image/*'],
        }

    def detect_file_type(self, file: File) -> Optional[str]:
        return 'image'
