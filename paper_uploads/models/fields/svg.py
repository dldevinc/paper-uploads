from ... import forms
from .base import FileResourceFieldBase


class SVGFileField(FileResourceFieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("to", "paper_uploads.UploadedSVGFile")
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": forms.FileField, **kwargs})
