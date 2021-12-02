from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class StandardCollection(Collection):
    """ Implicit proxy model on Collection """
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)


class Page(models.Model):
    collection = CollectionField(
        StandardCollection,
        verbose_name=_("collection")
    )

    class Meta:
        verbose_name = _("Page")
