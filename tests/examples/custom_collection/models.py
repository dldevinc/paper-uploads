from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class CustomCollection(Collection):
    image = CollectionItem(ImageItem)

    # addition field
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        # must be explicitly declared
        proxy = False


class CustomSubCollection(CustomCollection):
    svg = CollectionItem(SVGItem)


class Page(models.Model):
    gallery = CollectionField(
        CustomCollection,
        verbose_name=_("gallery")
    )

    class Meta:
        verbose_name = _("Page")
