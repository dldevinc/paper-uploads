from .... import forms
from ....models.fields.base import FileResourceFieldBase
from .base import CloudinaryOptionsMixin


class CloudinaryImageField(CloudinaryOptionsMixin, FileResourceFieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("to", "paper_uploads_cloudinary.CloudinaryImage")
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": forms.ImageField, **kwargs})
