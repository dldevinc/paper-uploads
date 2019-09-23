from .base import UploadedFileBaseForm
from ...models import UploadedFile


class UploadedFileDialog(UploadedFileBaseForm):
    class Meta:
        model = UploadedFile
        fields = ('new_name', 'display_name')
