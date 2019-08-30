from django.core import checks
from .base import FileFieldBase
from ..image import UploadedImage
from ... import forms
from ... import utils


class ImageField(FileFieldBase):
    def __init__(self, *args, variations=None, **kwargs):
        kwargs.setdefault('to', UploadedImage)
        self.variations = utils.build_variations(variations)
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_variations(**kwargs)
        ]

    def _check_variations(self, **kwargs):
        if not self.variations:
            return []
        for name, variation in self.variations.items():
            if name.startswith('_'):
                return [
                    checks.Error(
                        "Variation name can\'t starts with '_': %s" % name,
                        obj=self,
                    )
                ]
        return []

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'variations' in kwargs:
            del kwargs['variations']
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.ImageField,
            'owner_app_label': self.opts.app_label.lower(),
            'owner_model_name': self.opts.model_name.lower(),
            'owner_fieldname': self.name,
            **kwargs
        })
