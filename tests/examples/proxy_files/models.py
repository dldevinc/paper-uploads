from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class UploadedFileProxy(UploadedFile):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        # change output folder
        return "proxy-files/%Y-%m-%d"


class UploadedImageProxy(UploadedImage):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        # change output folder
        return "proxy-images/%Y-%m-%d"


class Page(models.Model):
    file = FileField(
        _("file"),
        to=UploadedFileProxy,
        blank=True,
    )
    image = ImageField(
        _("image"),
        to=UploadedImageProxy,
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
