from django import forms

from app.models.custom import CustomImageItem
from paper_uploads.forms.dialogs.collection import ImageItemDialog


class CustomImageItemDialog(ImageItemDialog):
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
