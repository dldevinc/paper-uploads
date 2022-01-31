from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class CustomUploadedFile(UploadedFileBase):
    change_form_class = "examples.custom_files.dialogs.ChangeCustomUploadedFileDialog"

    # addition field
    author = models.CharField(
        _("author"),
        max_length=128,
        blank=True
    )


class CustomUploadedImage(UploadedImageBase):
    change_form_class = "examples.custom_files.dialogs.ChangeCustomUploadedImageDialog"

    # addition field
    author = models.CharField(
        _("author"),
        max_length=128,
        blank=True
    )


class Page(models.Model):
    file = FileField(
        _("file"),
        to=CustomUploadedFile,
        blank=True
    )
    image = ImageField(
        _("image"),
        to=CustomUploadedImage,
        blank=True
    )

    class Meta:
        verbose_name = _("Page")
