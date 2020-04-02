from ... import forms
from ...models.fields import FileFieldBase


class CloudinaryOptionsMixin:
    def __init__(self, *args, cloudinary=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cloudinary_options = cloudinary

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'cloudinary' in kwargs:
            del kwargs['public_id']
        return name, path, args, kwargs


class CloudinaryFileField(CloudinaryOptionsMixin, FileFieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('to', 'paper_uploads_cloudinary.CloudinaryFile')
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.FileField,
            **kwargs
        })


class CloudinaryImageField(CloudinaryOptionsMixin, FileFieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('to', 'paper_uploads_cloudinary.CloudinaryImage')
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.ImageField,
            **kwargs
        })


class CloudinaryMediaField(CloudinaryOptionsMixin, FileFieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('to', 'paper_uploads_cloudinary.CloudinaryMedia')
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.FileField,
            **kwargs
        })
