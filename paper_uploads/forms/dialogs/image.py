from django import forms

from ...models.image import UploadedImage
from .base import ChangeFileResourceDialogBase


class ChangeUploadedImageDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = UploadedImage
        fields = ["new_name", "title", "description"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 2
            })
        }
