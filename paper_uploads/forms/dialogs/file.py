from ...models.file import UploadedFile
from .base import ChangeFileResourceDialogBase


class ChangeUploadedFileDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = UploadedFile
        fields = ["new_name", "display_name"]
