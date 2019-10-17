from .base import FileFieldBase
from ..file import UploadedFile
from ... import forms


class FileField(FileFieldBase):
    def __init__(self, *args, postprocess=None, **kwargs):
        kwargs.setdefault('to', UploadedFile)
        super().__init__(*args, **kwargs)
        self.postprocess = postprocess

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'postprocess' in kwargs:
            del kwargs['postprocess']
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.FileField,
            **kwargs
        })
