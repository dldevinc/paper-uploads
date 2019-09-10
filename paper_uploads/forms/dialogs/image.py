from .base import UploadedFileBaseForm
from ...models import UploadedImage


class UploadedImageDialog(UploadedFileBaseForm):
    class Meta:
        model = UploadedImage
        fields = ('new_name', 'alt', 'title')
