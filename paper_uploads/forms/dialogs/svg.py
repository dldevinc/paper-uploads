from django import forms

from ...models.svg import UploadedSVGFile
from .base import ChangeFileResourceDialogBase


class ChangeUploadedSVGFileDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = UploadedSVGFile
        fields = ["new_name", "display_name", "title", "description"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 2
            })
        }
