from typing import Any, Dict

from django.core.files.storage import Storage
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from ..conf import settings
from ..helpers import build_variations
from ..storage import default_storage
from ..utils import cached_method, filesizeformat
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

    @classmethod
    def get_file_field(cls) -> VariationalFileField:
        return cls._meta.get_field("file")

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

    @cached_method("_variations_cache")
    def get_variations(self) -> Dict[str, PaperVariation]:
        owner_field = self.get_owner_field()
        if owner_field is None:
            raise cached_method.Bypass({})

        variation_config = getattr(owner_field, "variations", {}).copy()
        return build_variations(variation_config)

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
