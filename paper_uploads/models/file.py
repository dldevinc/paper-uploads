import posixpath
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from .base import UploadedFileBase, SlaveModelMixin
from ..storage import upload_storage
from ..conf import settings
from .. import utils


class UploadedFile(UploadedFileBase, SlaveModelMixin):
    file = models.FileField(_('file'), max_length=255,
        upload_to=settings.FILES_UPLOAD_TO, storage=upload_storage)
    display_name = models.CharField(_('display name'), max_length=255, blank=True)

    class Meta(UploadedFileBase.Meta):
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def pre_save_new_file(self):
        super().pre_save_new_file()
        if not self.pk and not self.display_name:
            self.display_name = self.name

    def post_save_new_file(self):
        super().post_save_new_file()
        # TODO: надо как-то изящнее это делать
        filename, ext = posixpath.splitext(self.file.name)
        if ext.lower() == '.svg':
            utils.postprocess_svg(self.file.name)

    def as_dict(self):
        return {
            **super().as_dict(),
            'name': self.display_name,
            'file_info': '({ext}, {size})'.format(
                ext=self.extension,
                size=filesizeformat(self.size)
            ),
        }
