from .base import UploadedFileBaseForm
from ...models import GalleryFileItem, GalleryImageItem


class FileItemDialog(UploadedFileBaseForm):
    class Meta:
        model = GalleryFileItem
        fields = ('new_name', 'display_name')


class ImageItemDialog(UploadedFileBaseForm):
    class Meta:
        model = GalleryImageItem
        fields = ('new_name', 'alt', 'title')
