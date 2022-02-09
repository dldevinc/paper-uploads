from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class CustomUploadedFile(UploadedFileBase):
    change_form_class = "examples.fields.custom_models.dialogs.ChangeCustomUploadedFileDialog"

    # addition field
    author = models.CharField(
        _("author"),
        max_length=128,
        blank=True,
    )


class CustomUploadedImage(UploadedImageBase):
    change_form_class = "examples.fields.custom_models.dialogs.ChangeCustomUploadedImageDialog"

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
        blank=True,
        upload_to="custom-files/%Y-%m-%d"
    )
    image = ImageField(
        _("image"),
        to=CustomUploadedImage,
        blank=True,
        upload_to="custom-images/%Y-%m-%d",
        variations=dict(
            desktop=dict(
                size=(800, 0),
                clip=False
            ),
            mobile=dict(
                size=(0, 600),
                clip=False
            ),
        )
    )

    class Meta:
        verbose_name = _("Page")
