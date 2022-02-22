from typing import Any, Dict

from django.core.files.storage import Storage
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from ..conf import settings
from ..helpers import build_variations
from ..storage import default_storage
from ..utils import filesizeformat
from ..variations import PaperVariation
from .base import FileFieldResource, VersatileImageResourceMixin
from .fields import VariationalFileField
from .mixins import BacklinkModelMixin, EditableResourceMixin


class UploadedImageBase(VersatileImageResourceMixin, BacklinkModelMixin, EditableResourceMixin, FileFieldResource):
    change_form_class = "paper_uploads.forms.dialogs.image.ChangeUploadedImageDialog"

    file = VariationalFileField(
        _("file"),
        max_length=255,
    )

    class Meta(FileFieldResource.Meta):
        abstract = True
        verbose_name = _("image")
        verbose_name_plural = _("images")

    def get_file_folder(self) -> str:
        owner_field = self.get_owner_field()
        return getattr(owner_field, "upload_to", "") or settings.IMAGES_UPLOAD_TO

    def get_file_storage(self) -> Storage:
        owner_field = self.get_owner_field()
        storage = getattr(owner_field, "storage", None) or default_storage
        if callable(storage):
            storage = storage()
        return storage

    def get_file(self) -> FieldFile:
        return self.file

    def get_file_field(self) -> VariationalFileField:
        return self._meta.get_field("file")

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "file_info": "({ext}, {width}x{height}, {size})".format(
                ext=self.extension,
                width=self.width,
                height=self.height,
                size=filesizeformat(self.size),
            ),
        }

    def get_variations(self) -> Dict[str, PaperVariation]:
        if not hasattr(self, "_variations_cache"):
            owner_field = self.get_owner_field()
            if owner_field is not None:
                variation_config = getattr(owner_field, "variations", {}).copy()
                self._variations_cache = build_variations(variation_config)
            else:
                return {}
        return self._variations_cache

    @classmethod
    def get_configuration(cls) -> Dict[str, Any]:
        return {
            "strictImageValidation": True,
            "acceptFiles": [
                "image/bmp",
                "image/gif",
                "image/jpeg",
                "image/png",
                # "image/svg+xml",
                "image/tiff",
                "image/webp",
            ],
        }


class UploadedImage(UploadedImageBase):
    class Meta(UploadedImageBase.Meta):
        pass
