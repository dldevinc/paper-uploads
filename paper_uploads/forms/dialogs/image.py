from django import forms

from ...models.image import UploadedImage
from .base import UploadedFileBaseForm


class UploadedImageDialog(UploadedFileBaseForm):
    class Meta:
        model = UploadedImage
        fields = ("new_name", "title", "description")
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 3
            })
        }
