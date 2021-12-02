from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class CustomImageItem(ImageItemBase):  # <-- inherit from `ImageItemBase`! Not `ImageItem`!
    collectionitembase_ptr = models.OneToOneField(
        CollectionItemBase,
        parent_link=True,
        on_delete=models.CASCADE,
        related_name='+'  # Fix 'reverse accessor clashes ...' error
    )

    # addition field
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def get_file_folder(self) -> str:
        # change output folder
        return "collections/custom-images/%Y-%m-%d"


class CollectionDefinition(Collection):
    image = CollectionItem(CustomImageItem)


class Page(models.Model):
    gallery = CollectionField(
        CollectionDefinition,
        verbose_name=_("gallery")
    )

    class Meta:
        verbose_name = _("Page")
