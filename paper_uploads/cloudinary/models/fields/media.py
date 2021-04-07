from .... import forms
from ....models.fields.base import FileResourceFieldBase
from .base import CloudinaryOptionsMixin


class CloudinaryMediaField(CloudinaryOptionsMixin, FileResourceFieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("to", "paper_uploads_cloudinary.CloudinaryMedia")
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": forms.FileField, **kwargs})
