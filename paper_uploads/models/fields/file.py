from ... import forms
from .base import FileFieldBase


class FileField(FileFieldBase):
    def __init__(self, *args, postprocess=None, **kwargs):
        kwargs.setdefault('to', 'paper_uploads.UploadedFile')
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
