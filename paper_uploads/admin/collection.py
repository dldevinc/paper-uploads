from django.urls import path

from .. import views
from .base import UploadedFileBase


class CollectionAdminBase(UploadedFileBase):
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path(
                'create/',
                self.admin_site.admin_view(views.collection.create_collection),
                name='%s_%s_create' % info,
            ),
            path(
                'delete/',
                self.admin_site.admin_view(views.collection.delete_collection),
                name='%s_%s_delete' % info,
            ),
            path(
                'upload_item/',
                self.admin_site.admin_view(views.collection.upload_item),
                name='%s_%s_upload_item' % info,
            ),
            path(
                'change_item/',
                self.admin_site.admin_view(views.collection.ChangeView.as_view()),
                name='%s_%s_change_item' % info,
            ),
            path(
                'delete_item/',
                self.admin_site.admin_view(views.collection.delete_item),
                name='%s_%s_delete_item' % info,
            ),
            path(
                'sort_items/',
                self.admin_site.admin_view(views.collection.sort_items),
                name='%s_%s_sort_items' % info,
            ),
        ]
        return urlpatterns
