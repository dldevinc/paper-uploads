import os
import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class UploadedFileProxy(UploadedFile):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "proxy-files/%Y-%m-%d"


class UploadedImageProxy(UploadedImage):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "proxy-images/%Y-%m-%d"


class CustomUploadedFileProxy(UploadedFile):
    class Meta:
        proxy = True

    def generate_filename(self, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        filename = "custom-proxy-files/file-%Y-%m-%d_%H%M%S{}".format(ext)
        filename = datetime.datetime.now().strftime(filename)

        storage = self.get_file_storage()
        return storage.generate_filename(filename)


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

    custom_file = FileField(
        _("custom file"),
        to=CustomUploadedFileProxy,
        blank=True,
    )

    class Meta:
        verbose_name = _("Page")
