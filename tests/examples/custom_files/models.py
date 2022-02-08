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

    def get_file_folder(self) -> str:
        # change output folder
        return "custom-files/%Y-%m-%d"


class CustomUploadedImage(UploadedImageBase):
    change_form_class = "examples.custom_files.dialogs.ChangeCustomUploadedImageDialog"

    # addition field
    author = models.CharField(
        _("author"),
        max_length=128,
        blank=True
    )

    def get_file_folder(self) -> str:
        # change output folder
        return "custom-images/%Y-%m-%d"


class Page(models.Model):
    file = FileField(
        _("file"),
        to=CustomUploadedFile,
        blank=True
    )
    image = ImageField(
        _("image"),
        to=CustomUploadedImage,
        blank=True,
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
