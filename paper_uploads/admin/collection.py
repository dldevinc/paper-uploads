from django.urls import path

from .. import views
from .base import UploadedFileBase


class CollectionAdminBase(UploadedFileBase):
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path(
                "create/",
                self.admin_site.admin_view(views.collection.CreateCollectionView.as_view()),
                name="%s_%s_create" % info,
            ),
            path(
                "delete/",
                self.admin_site.admin_view(views.collection.DeleteCollectionView.as_view()),
                name="%s_%s_delete" % info,
            ),
            path(
                "upload_item/",
                self.admin_site.admin_view(views.collection.UploadFileView.as_view()),
                name="%s_%s_upload_item" % info,
            ),
            path(
                "delete_item/",
                self.admin_site.admin_view(views.collection.DeleteFileView.as_view()),
                name="%s_%s_delete_item" % info,
            ),
            path(
                "change_item/",
                self.admin_site.admin_view(views.collection.ChangeFileView.as_view()),
                name="%s_%s_change_item" % info,
            ),
            path(
                "sort_items/",
                self.admin_site.admin_view(views.collection.SortItemsView.as_view()),
                name="%s_%s_sort_items" % info,
            ),
        ]
        return urlpatterns
