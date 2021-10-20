from django.contrib import admin
from django.urls import path

from .. import views
from ..models.file import UploadedFile
from .base import UploadedFileBase


@admin.register(UploadedFile)
class UploadedFileAdmin(UploadedFileBase):
    upload_view_class = views.file.UploadFileView
    delete_view_class = views.file.DeleteFileView
    change_view_class = views.file.ChangeFileView

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path(
                "upload/",
                self.admin_site.admin_view(self.upload_view_class.as_view()),
                name="%s_%s_upload" % info,
            ),
            path(
                "delete/",
                self.admin_site.admin_view(self.delete_view_class.as_view()),
                name="%s_%s_delete" % info,
            ),
            path(
                "change/",
                self.admin_site.admin_view(self.change_view_class.as_view()),
                name="%s_%s_change" % info,
            ),
        ]
        return urlpatterns
