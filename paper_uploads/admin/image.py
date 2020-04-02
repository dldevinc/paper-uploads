from django.contrib import admin
from django.urls import path

from .. import views
from ..models.image import UploadedImage
from .base import UploadedFileBase


@admin.register(UploadedImage)
class UploadedImageAdmin(UploadedFileBase):
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path(
                'upload/',
                self.admin_site.admin_view(views.image.upload),
                name='%s_%s_upload' % info,
            ),
            path(
                'change/',
                self.admin_site.admin_view(views.image.ChangeView.as_view()),
                name='%s_%s_change' % info,
            ),
            path(
                'delete/',
                self.admin_site.admin_view(views.image.delete),
                name='%s_%s_delete' % info,
            ),
        ]
        return urlpatterns
