import io
import os
import tempfile

from django.core import checks
from django.core.exceptions import SuspiciousFileOperation
from django.core.files import File
from django.db import models
from django.utils.crypto import get_random_string
from filelock import FileLock, Timeout

from ... import forms
from ...helpers import build_variations
from ...typing import VariationConfig
from .base import FileResourceFieldBase


class VariationalFileField(models.FileField):
    """
    Из-за того, что вариация может самостоятельно установить свой формат,
    возможна ситуация, когда вариации одного изображения перезапишут вариации
    другого. Например, когда загружаются файлы, отличающиеся только расширением.
    Поэтому мы проверяем все имена будущих вариаций на существование, чтобы
    не допустить перезапись.
    """

    def _variations_collapsed(self, instance, name):
        if self.storage.exists(name):
            return True

        for variation in instance.get_variations().values():
            variation_filename = variation.get_output_filename(name)
            if self.storage.exists(variation_filename):
                return True
        return False

    def _find_available_name(self, instance, name):
        max_length = self.max_length
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        while self._variations_collapsed(instance, name) or (
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
                        "Storage cannot find an available filename for '%s'. "
                        "Please make sure the corresponding file field "
                        "allows sufficient 'max_length'." % name
                    )
                name = os.path.join(
                    dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext)
                )
        return name

    def _create_placeholder_files(self, instance, name):
        """
        Создаем файлы-заглушки, которые "забронируют" имена
        итоговых файлов вариаций.

        Разрешает ситуацию, когда два или более файлов с одинаковым
        именем, но разными расширением загружаются одновременно
        в разных процессах / потоках.
        """
        buffer = File(io.BytesIO(b"dummy"))
        for variation in instance.get_variations().values():
            variation_filename = variation.get_output_filename(name)
            self.storage.save(variation_filename, buffer)

    def generate_filename(self, instance, filename):
        name = super().generate_filename(instance, filename)
        lock = FileLock(os.path.join(tempfile.gettempdir(), "paper_uploads.lock"))
        try:
            with lock.acquire(timeout=5):
                available_name = self._find_available_name(instance, name)
                self._create_placeholder_files(instance, available_name)
        except Timeout:
            available_name = self._find_available_name(instance, name)
        return available_name


class ImageField(FileResourceFieldBase):
    def __init__(self, *args, variations: VariationConfig = None, **kwargs):
        kwargs.setdefault("to", "paper_uploads.UploadedImage")
        self.variations = build_variations(variations or {})
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        return [*super().check(**kwargs), *self._check_variations()]

    def _check_variations(self):
        if not self.variations:
            return []
        for name, variation in self.variations.items():
            if name.startswith("_"):
                return [
                    checks.Error(
                        "Variation name can\'t starts with '_': %s" % name, obj=self,
                    )
                ]
        return []

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if "variations" in kwargs:
            del kwargs["variations"]
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": forms.ImageField, **kwargs})
