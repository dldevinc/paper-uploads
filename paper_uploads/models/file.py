from typing import Any, Dict

from django.db import models
from django.db.models.fields.files import FieldFile
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from ..conf import settings
from ..storage import upload_storage
from .base import FileFieldResource, ReadonlyFileProxyMixin, ReverseFieldModelMixin
from .fields import FormattedFileField


class UploadedFile(ReverseFieldModelMixin, ReadonlyFileProxyMixin, FileFieldResource):
    file = FormattedFileField(
        _('file'),
        max_length=255,
        storage=upload_storage,
        upload_to=settings.FILES_UPLOAD_TO,
    )
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(FileFieldResource.Meta):
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def save(self, *args, **kwargs):
        if not self.pk and not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def get_file(self) -> FieldFile:
        return self.file

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.display_name,
            'file_info': '({ext}, {size})'.format(
                ext=self.extension, size=filesizeformat(self.size)
            ),
        }
