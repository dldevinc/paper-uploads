from ...models.fields.file import FileFieldBase
from ... import forms


class CloudinaryFileField(FileFieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('to', 'paper_uploads_cloudinary.CloudinaryFile')
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.FileField,
            **kwargs
        })


class CloudinaryImageField(FileFieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('to', 'paper_uploads_cloudinary.CloudinaryImage')
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.ImageField,
            **kwargs
        })
