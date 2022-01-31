from typing import Any, Dict

from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from ..conf import settings
from ..storage import upload_storage
from ..utils import filesizeformat
from .base import FileFieldResource
from .mixins import BacklinkModelMixin, EditableResourceMixin
from .utils import generate_filename


class UploadedFileBase(BacklinkModelMixin, EditableResourceMixin, FileFieldResource):
    change_form_class = "paper_uploads.forms.dialogs.file.ChangeUploadedFileDialog"

    file = models.FileField(
        _("file"),
        max_length=255,
        storage=upload_storage,
        upload_to=generate_filename,
    )
    display_name = models.CharField(_("display name"), max_length=255, blank=True)

    class Meta(FileFieldResource.Meta):
        abstract = True
        verbose_name = _("file")
        verbose_name_plural = _("files")

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.basename
        super().save(*args, **kwargs)

    def get_file_folder(self) -> str:
        return settings.FILES_UPLOAD_TO

    def get_file(self) -> FieldFile:
        return self.file

    def set_file(self, value):
        self.file = value

    def get_file_field(self) -> models.FileField:
        return self._meta.get_field("file")

    def get_caption(self) -> str:
        name = self.display_name or self.basename
        if self.extension:
            return "{}.{}".format(name, self.extension)
        return name

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.display_name,
            "file_info": "({ext}, {size})".format(
                ext=self.extension, size=filesizeformat(self.size)
            ),
        }


class UploadedFile(UploadedFileBase):
    class Meta(UploadedFileBase.Meta):
        pass
