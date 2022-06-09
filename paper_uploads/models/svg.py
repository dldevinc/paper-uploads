from typing import Any, Dict

from django.core.files.storage import Storage
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from ..conf import settings
from ..storage import default_storage
from ..utils import filesizeformat
from .base import FileFieldResource, SVGFileResourceMixin
from .fields.base import DynamicStorageFileField
from .mixins import BacklinkModelMixin, EditableResourceMixin


class UploadedSVGFileBase(SVGFileResourceMixin, BacklinkModelMixin, EditableResourceMixin, FileFieldResource):
    change_form_class = "paper_uploads.forms.dialogs.svg.ChangeUploadedSVGFileDialog"

    file = DynamicStorageFileField(
        _("file"),
        max_length=255,
    )
    display_name = models.CharField(
        _("display name"),
        max_length=255,
        blank=True
    )

    class Meta(FileFieldResource.Meta):
        abstract = True
        verbose_name = _("SVG file")
        verbose_name_plural = _("SVG files")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.resource_name
        super().save(*args, **kwargs)

    def get_file_folder(self) -> str:
        owner_field = self.get_owner_field()
        return getattr(owner_field, "upload_to", "") or settings.FILES_UPLOAD_TO

    def get_file_storage(self) -> Storage:
        owner_field = self.get_owner_field()
        storage = getattr(owner_field, "storage", None) or default_storage
        if callable(storage):
            storage = storage()
        return storage

    def get_file(self) -> FieldFile:
        return self.file

    @classmethod
    def get_file_field(cls) -> models.FileField:
        return cls._meta.get_field("file")

    def get_caption(self) -> str:
        name = self.display_name or self.resource_name
        if self.extension:
            return "{}.{}".format(name, self.extension)
        return name

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.display_name or self.resource_name,
            "file_info": "({ext}, {size})".format(
                ext=self.extension, size=filesizeformat(self.size)
            ),
        }

    @classmethod
    def get_configuration(cls) -> Dict[str, Any]:
        return {
            "acceptFiles": [
                "image/svg+xml",
            ],
        }


class UploadedSVGFile(UploadedSVGFileBase):
    class Meta(UploadedSVGFileBase.Meta):
        pass
