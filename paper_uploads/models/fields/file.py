from .base import FileFieldBase
from ..file import UploadedFile
from ... import forms


class FileField(FileFieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('to', UploadedFile)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.FileField,
            'owner_app_label': self.opts.app_label.lower(),
            'owner_model_name': self.opts.model_name.lower(),
            'owner_fieldname': self.name,
            **kwargs
        })
