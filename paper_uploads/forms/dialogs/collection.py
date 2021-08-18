from django import forms

from ...models.collection import FileItem, ImageItem
from .base import UploadedFileBaseForm


class FileItemDialog(UploadedFileBaseForm):
    class Meta:
        model = FileItem
        fields = ("new_name", "display_name")


class ImageItemDialog(UploadedFileBaseForm):
    class Meta:
        model = ImageItem
        fields = ("new_name", "title", "description")
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 3
            })
        }
