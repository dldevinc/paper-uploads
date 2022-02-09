from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class ProxyImageItem(ImageItem):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        # change output folder
        return "collections/proxy-images/%Y-%m-%d"


class ProxyCollection(Collection):
    image = CollectionItem(ProxyImageItem)


class Page(models.Model):
    collection = CollectionField(
        ProxyCollection,
        verbose_name=_("collection")
    )

    class Meta:
        verbose_name = _("Page")
