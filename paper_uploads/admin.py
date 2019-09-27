from django.urls import path
from django.contrib import admin
from .models import UploadedFile, UploadedImage
from . import views


class UploadedFileBase(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def log_addition(self, *args, **kwargs):
        return

    def log_change(self, *args, **kwargs):
        return

    def log_deletion(self, *args, **kwargs):
        return


@admin.register(UploadedFile)
class UploadedFileAdmin(UploadedFileBase):
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path(
                'upload/',
                self.admin_site.admin_view(views.file.upload),
                name='%s_%s_upload' % info
            ),
            path(
                'change/',
                self.admin_site.admin_view(views.file.ChangeView.as_view()),
                name='%s_%s_change' % info
            ),
            path(
                'delete/',
                self.admin_site.admin_view(views.file.delete),
                name='%s_%s_delete' % info
            ),
        ]
        return urlpatterns


@admin.register(UploadedImage)
class UploadedImageAdmin(UploadedFileBase):
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path(
                'upload/',
                self.admin_site.admin_view(views.image.upload),
                name='%s_%s_upload' % info
            ),
            path(
                'change/',
                self.admin_site.admin_view(views.image.ChangeView.as_view()),
                name='%s_%s_change' % info
            ),
            path(
                'delete/',
                self.admin_site.admin_view(views.image.delete),
                name='%s_%s_delete' % info
            ),
        ]
        return urlpatterns


class CollectionAdminBase(UploadedFileBase):
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path(
                'delete/',
                self.admin_site.admin_view(views.collection.delete_collection),
                name='%s_%s_delete' % info
            ),
            path(
                'upload_item/',
                self.admin_site.admin_view(views.collection.upload_item),
                name='%s_%s_upload_item' % info
            ),
            path(
                'change_item/',
                self.admin_site.admin_view(views.collection.ChangeView.as_view()),
                name='%s_%s_change_item' % info
            ),
            path(
                'delete_item/',
                self.admin_site.admin_view(views.collection.delete_item),
                name='%s_%s_delete_item' % info
            ),
            path(
                'sort_items/',
                self.admin_site.admin_view(views.collection.sort_items),
                name='%s_%s_sort_items' % info
            ),
        ]
        return urlpatterns
