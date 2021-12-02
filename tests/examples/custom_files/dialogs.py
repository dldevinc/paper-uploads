from paper_uploads.forms.dialogs.file import ChangeUploadedFileDialog
from paper_uploads.forms.dialogs.image import ChangeUploadedImageDialog

from .models import CustomUploadedFile, CustomUploadedImage


class ChangeCustomUploadedFileDialog(ChangeUploadedFileDialog):
    class Meta(ChangeUploadedFileDialog.Meta):
        model = CustomUploadedFile
        fields = ChangeUploadedFileDialog.Meta.fields + ["author"]


class ChangeCustomUploadedImageDialog(ChangeUploadedImageDialog):
    class Meta(ChangeUploadedImageDialog.Meta):
        model = CustomUploadedImage
        fields = ChangeUploadedImageDialog.Meta.fields + ["author"]
