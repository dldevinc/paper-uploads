from django import forms

from ...models.collection import FileItem, SVGItem, ImageItem
from .base import ChangeFileResourceDialogBase


class ChangeFileItemDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = FileItem
        fields = ["new_name", "display_name"]


class ChangeSVGItemDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = SVGItem
        fields = ["new_name", "display_name", "title", "description"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 2
            })
        }


class ChangeImageItemDialog(ChangeFileResourceDialogBase):
    class Meta:
        model = ImageItem
        fields = ["new_name", "title", "description"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 2
            })
        }
