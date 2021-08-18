from ...models.file import UploadedFile
from .base import UploadedFileBaseForm


class UploadedFileDialog(UploadedFileBaseForm):
    class Meta:
        model = UploadedFile
        fields = ("new_name", "display_name")
