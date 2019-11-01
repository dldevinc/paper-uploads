import magic
import posixpath
from typing import Dict, Any
from django.db import models
from django.template import loader
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from cloudinary.models import CloudinaryField
from ...conf import settings
from ...models.base import UploadedFileBase
from ...models.image import UploadedImageBase
from ...models.fields import CollectionItemTypeField
from ...models.collection import FilePreviewItemMixin, CollectionResourceItem, Collection
from ..container import CloudinaryContainerMixin

__all__ = [
    'CloudinaryFileItem', 'CloudinaryImageItem', 'CloudinaryMediaItem',
    'CloudinaryCollection', 'CloudinaryImageCollection'
]


class CloudinaryCollectionFileItemMixin(CloudinaryContainerMixin, CollectionResourceItem):
    class Meta(CollectionResourceItem.Meta):
        abstract = True

    def attach_file(self, file: File, **options):
        # skip Cloudinary suffix
        basename = posixpath.basename(file.name)
        file_name, file_ext = posixpath.splitext(basename)
        self.name = file_name

        # set cloudinary options from field data
        item_type_field = self.get_itemtype_field()
        if item_type_field is not None:
            cloudinary_options = {
                'use_filename': item_type_field.options.get('use_filename', True),
                'unique_filename': item_type_field.options.get('unique_filename', True),
                'overwrite': item_type_field.options.get('overwrite', True),
            }
            public_id = item_type_field.options.get('public_id')
            if public_id is not None:
                self.cloudinary_options['public_id'] = public_id
            folder = item_type_field.options.get('folder')
            if folder is not None:
                self.cloudinary_options['folder'] = folder
            options.setdefault('cloudinary', cloudinary_options)

        super().attach_file(file, **options)


class CloudinaryFileItem(CloudinaryCollectionFileItemMixin, FilePreviewItemMixin, UploadedFileBase):
    change_form_class = 'paper_uploads.forms.dialogs.collection.FileItemDialog'
    admin_template_name = 'paper_uploads/collection_item/file.html'

    file = CloudinaryField(_('file'), resource_type='raw')
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(CollectionResourceItem.Meta):
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def __str__(self):
        return self.get_file_name()

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    @classmethod
    def file_supported(cls, file: File) -> bool:
        return True

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.canonical_name,
            'url': self.get_file_url(),
        }


class CloudinaryImageItem(CloudinaryCollectionFileItemMixin, UploadedImageBase):
    PREVIEW_VARIATIONS = settings.COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS
    change_form_class = 'paper_uploads.forms.dialogs.collection.ImageItemDialog'
    admin_template_name = 'paper_uploads_cloudinary/collection_item/image.html'
    cloudinary_resource_type = 'image'

    file = CloudinaryField(_('file'), resource_type='image')

    class Meta(CollectionResourceItem.Meta):
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def __str__(self):
        return self.get_file_name()

    @classmethod
    def file_supported(cls, file: File) -> bool:
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)    # correct file position after mimetype detection
        basetype, subtype = mimetype.split('/', 1)
        return basetype == 'image'

    def _post_attach_file(self, data=None):
        super()._post_attach_file(data)
        if isinstance(data, dict):
            if 'width' in data:
                self.width = data['width']
            if 'height' in data:
                self.height = data['height']

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.canonical_name,
            'url': self.get_file_url(),
            'preview': loader.render_to_string('paper_uploads_cloudinary/collection_item/preview/image.html', {
                'item': self,
                'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            })
        }


class CloudinaryMediaItem(CloudinaryCollectionFileItemMixin, FilePreviewItemMixin, UploadedFileBase):
    change_form_class = 'paper_uploads.forms.dialogs.collection.FileItemDialog'
    admin_template_name = 'paper_uploads/collection_item/file.html'
    cloudinary_resource_type = 'video'

    file = CloudinaryField(_('file'), resource_type='video')
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(CollectionResourceItem.Meta):
        verbose_name = _('media')
        verbose_name_plural = _('media')

    def __str__(self):
        return self.get_file_name()

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    @classmethod
    def file_supported(cls, file: File) -> bool:
        mimetype = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)    # correct file position after mimetype detection
        basetype, subtype = mimetype.split('/', 1)
        return basetype in {'video', 'audio'}

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.canonical_name,
            'url': self.get_file_url(),
        }


class CloudinaryCollection(Collection):
    image = CollectionItemTypeField(CloudinaryImageItem)
    media = CollectionItemTypeField(CloudinaryMediaItem)
    file = CollectionItemTypeField(CloudinaryFileItem)


class CloudinaryImageCollection(Collection):
    image = CollectionItemTypeField(CloudinaryImageItem)

    @classmethod
    def get_validation(cls) -> Dict[str, Any]:
        return {
            **super().get_validation(),
            'acceptFiles': ['image/*'],
        }

    def detect_file_type(self, file: File) -> str:
        return 'image'
