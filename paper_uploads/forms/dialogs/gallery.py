from .base import UploadedFileBaseForm
from ...models import GalleryFileItem, GalleryImageItem


class GalleryFileDialog(UploadedFileBaseForm):
    class Meta:
        model = GalleryFileItem
        fields = ('new_name', 'display_name')


class GalleryImageDialog(UploadedFileBaseForm):
    class Meta:
        model = GalleryImageItem
        fields = ('new_name', 'alt', 'title')
