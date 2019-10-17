from typing import Dict, Any
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from .base import UploadedFileBase, SlaveModelMixin, ProxyFileAttributesMixin
from ..conf import settings
from ..storage import upload_storage
from ..postprocess import postprocess_uploaded_file


class UploadedFile(ProxyFileAttributesMixin, SlaveModelMixin, UploadedFileBase):
    file = models.FileField(_('file'), max_length=255,
        upload_to=settings.FILES_UPLOAD_TO, storage=upload_storage)
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(UploadedFileBase.Meta):
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def __str__(self):
        return self.file.name

    def pre_save_new_file(self):
        super().pre_save_new_file()
        if not self.pk and not self.display_name:
            self.display_name = self.name

    def post_save_new_file(self):
        super().post_save_new_file()
        owner_field = self.get_owner_field()
        postprocess_uploaded_file(self.file.name, owner_field)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.display_name,
            'file_info': '({ext}, {size})'.format(
                ext=self.extension,
                size=filesizeformat(self.size)
            ),
        }
