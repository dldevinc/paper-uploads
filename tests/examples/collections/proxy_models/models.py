import datetime
import os

from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class ProxyImageItem(ImageItem):
    class Meta:
        proxy = True

    def generate_filename(self, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        filename = "collections/proxy-images/image-%Y-%m-%d_%H%M%S{}".format(ext)
        filename = datetime.datetime.now().strftime(filename)

        storage = self.get_file_storage()
        return storage.generate_filename(filename)


class ProxyCollection(Collection):
    image = CollectionItem(ProxyImageItem)


class Page(models.Model):
    collection = CollectionField(
        ProxyCollection,
        verbose_name=_("collection")
    )

    class Meta:
        verbose_name = _("Page")
