from django import forms

from app.models.custom import CustomImageItem, CustomUploadedFile, CustomUploadedImage
from paper_uploads.forms.dialogs.base import ChangeFileResourceDialogBase


class CustomUploadedFileDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = CustomUploadedFile
        fields = ("new_name", "display_name", "author")


class CustomUploadedImageDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = CustomUploadedImage
        fields = ("new_name", "title", "description", "author")
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 3
            })
        }


class CustomImageItemDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = CustomImageItem
        fields = ("new_name", "caption", "title", "description")
        widgets = {
            "caption": forms.Textarea(attrs={
                "rows": 2
            }),
            "description": forms.Textarea(attrs={
                "rows": 3
            })
        }
