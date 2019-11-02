from .base import UploadedFileBaseForm
from ...models.image import UploadedImage


class UploadedImageDialog(UploadedFileBaseForm):
    class Meta:
        model = UploadedImage
        fields = ('new_name', 'title', 'description')
