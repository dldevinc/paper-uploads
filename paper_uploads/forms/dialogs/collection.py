from django import forms

from ...models.collection import FileItem, ImageItem
from .base import ChangeFileResourceDialogBase


class ChangeFileItemDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = FileItem
        fields = ["new_name", "display_name"]


class ChangeImageItemDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = ImageItem
        fields = ["new_name", "title", "description"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 2
            })
        }
