from ...models.fields import FileFieldBase
from ... import forms


class CloudinaryOptionsMixin:
    def __init__(self, *args, public_id=None, folder=None, use_filename=True,
            unique_filename=True, overwrite=True, **kwargs):
        super().__init__(*args, **kwargs)

        self.cloudinary_options = {
            'use_filename': use_filename,
            'unique_filename': unique_filename,
            'overwrite': overwrite,
        }
        if public_id is not None:
            self.cloudinary_options['public_id'] = public_id
        if folder is not None:
            self.cloudinary_options['folder'] = folder

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'public_id' in kwargs:
            del kwargs['public_id']
        if 'folder' in kwargs:
            del kwargs['folder']
        if 'use_filename' in kwargs:
            del kwargs['use_filename']
        if 'unique_filename' in kwargs:
            del kwargs['unique_filename']
        if 'overwrite' in kwargs:
            del kwargs['overwrite']
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
