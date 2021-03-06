from django.contrib import admin
from django.urls import path

from .. import views
from ..models.file import UploadedFile
from .base import UploadedFileBase


@admin.register(UploadedFile)
class UploadedFileAdmin(UploadedFileBase):
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path(
                'upload/',
                self.admin_site.admin_view(views.file.UploadFileView.as_view()),
                name='%s_%s_upload' % info,
            ),
            path(
                'delete/',
                self.admin_site.admin_view(views.file.DeleteFileView.as_view()),
                name='%s_%s_delete' % info,
            ),
            path(
                'change/',
                self.admin_site.admin_view(views.file.ChangeFileView.as_view()),
                name='%s_%s_change' % info,
            ),
        ]
        return urlpatterns
