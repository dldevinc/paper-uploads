from .base import UploadedFileBaseForm
from ...models import FileItem, ImageItem


class FileItemDialog(UploadedFileBaseForm):
    class Meta:
        model = FileItem
        fields = ('new_name', 'display_name')


class ImageItemDialog(UploadedFileBaseForm):
    class Meta:
        model = ImageItem
        fields = ('new_name', 'title', 'description')
