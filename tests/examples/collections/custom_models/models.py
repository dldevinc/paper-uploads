from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *


class ImageItem(ImageItemBase):
    change_form_class = "examples.collections.custom_models.dialogs.ChangeUploadedCustomImageDialog"

    # Предотвращение ошибки конфликта имён в случае существования
    # других моделей элемента коллекции с таким же именем.
    collectionitembase_ptr = models.OneToOneField(
        CollectionItemBase,
        parent_link=True,
        on_delete=models.CASCADE,
        related_name='+'  # Fix 'reverse accessor clashes ...' error
    )

    # addition fields
    caption = models.TextField(_("caption"), blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def get_file_folder(self) -> str:
        # change output folder
        return "collections/custom-images/%Y-%m-%d"


class CustomCollection(ImageCollection):
    image = CollectionItem(ImageItem)

    # addition field
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        # must be explicitly declared
        proxy = False


class Page(models.Model):
    collection = CollectionField(
        CustomCollection,
        verbose_name=_("collection")
    )

    class Meta:
        verbose_name = _("Page")
