import os
from typing import Any, Dict

from django.core import checks
from django.core.exceptions import SuspiciousFileOperation
from django.utils.crypto import get_random_string

from ... import forms
from ...helpers import build_variations
from .base import FileFieldBase, FormattedFileField


class VariationalFileField(FormattedFileField):
    """
    Из-за того, что вариация может самостоятельно установить свой формат,
    возможна ситуация, когда вариации одного изображения перезапишут вариации
    другого. Например, когда загружаются файлы, отличающиеся только расширением.
    Поэтому мы проверяем все имена будущих вариаций на существование, чтобы
    не допустить перезапись.
    """

    def variations_collapsed(self, instance, name):
        if self.storage.exists(name):
            return True

        for variation in instance.get_variations().values():
            variation_filename = variation.get_output_filename(name)
            if self.storage.exists(variation_filename):
                return True
        return False

    def generate_filename(self, instance, filename):
        name = super().generate_filename(instance, filename)

        max_length = self.max_length
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        while self.variations_collapsed(instance, name) or (
            max_length and len(name) > max_length
        ):
            name = os.path.join(
                dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext)
            )
            if max_length is None:
                continue
            # Truncate file_root if max_length exceeded.
            truncation = len(name) - max_length
            if truncation > 0:
                file_root = file_root[:-truncation]
                if not file_root:
                    raise SuspiciousFileOperation(
                        'Storage cannot find an available filename for "%s". '
                        'Please make sure the corresponding file field '
                        'allows sufficient "max_length".' % name
                    )
                name = os.path.join(
                    dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext)
                )
        return name


class ImageField(FileFieldBase):
    def __init__(self, *args, variations: Dict[str, Any] = None, **kwargs):
        kwargs.setdefault('to', 'paper_uploads.UploadedImage')
        self.variations = build_variations(variations or {})
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
                        "Variation name can\'t starts with '_': %s" % name, obj=self,
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
            **kwargs
        })
