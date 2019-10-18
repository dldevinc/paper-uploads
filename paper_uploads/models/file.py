from typing import Dict, Any
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from ..conf import settings
from ..storage import upload_storage
from ..postprocess import postprocess_common_file
from .. import tasks
from .base import UploadedFileBase, SlaveModelMixin, ProxyFileAttributesMixin


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
        self._postprocess()

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'name': self.display_name,
            'file_info': '({ext}, {size})'.format(
                ext=self.extension,
                size=filesizeformat(self.size)
            ),
        }

    def _postprocess_sync(self):
        owner_field = self.get_owner_field()
        postprocess_common_file(self.file.name, owner_field)

        current_hash_value = self.hash
        self.update_hash(commit=False)
        if current_hash_value and current_hash_value != self.hash:
            self.size = self.file.size
            self.update_hash(commit=False)
            self.modified_at = now()
            self.save(update_fields=['size', 'hash', 'modified_at'])

    def _postprocess_async(self):
        from django_rq.queues import get_queue
        queue = get_queue(settings.RQ_QUEUE_NAME)
        queue.enqueue_call(tasks.postprocess_file, kwargs={
            'app_label': self._meta.app_label,
            'model_name': self._meta.model_name,
            'object_id': self.pk,
            'using': self._state.db,
        })

    def _postprocess(self):
        if settings.RQ_ENABLED:
            self._postprocess_async()
        else:
            self._postprocess_sync()
