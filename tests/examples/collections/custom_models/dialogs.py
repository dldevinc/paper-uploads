from django import forms

from paper_uploads.forms.dialogs.base import ChangeFileResourceDialogBase

from .models import ImageItem


class ChangeUploadedCustomImageDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = ImageItem
        fields = ["new_name", "caption", "title", "description"]
        widgets = {
            "caption": forms.Textarea(attrs={
                "rows": 2
            }),
            "description": forms.Textarea(attrs={
                "rows": 3
            })
        }
