from django.contrib import admin
from django.urls import path

from .. import views
from ..models.collection import Collection
from .base import ResourceAdminBase


class CollectionAdminBase(ResourceAdminBase):
    create_collection_view_class = views.collection.CreateCollectionView
    delete_collection_view_class = views.collection.DeleteCollectionView
    upload_item_view_class = views.collection.UploadFileView
    delete_item_view_class = views.collection.DeleteFileView
    change_item_view_class = views.collection.ChangeFileView
    sort_items_view_class = views.collection.SortItemsView

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path(
                "create/",
                self.admin_site.admin_view(self.create_collection_view_class.as_view()),
                name="%s_%s_create" % info,
            ),
            path(
                "delete/",
                self.admin_site.admin_view(self.delete_collection_view_class.as_view()),
                name="%s_%s_delete" % info,
            ),
            path(
                "upload-item/",
                self.admin_site.admin_view(self.upload_item_view_class.as_view()),
                name="%s_%s_upload_item" % info,
            ),
            path(
                "delete-item/",
                self.admin_site.admin_view(self.delete_item_view_class.as_view()),
                name="%s_%s_delete_item" % info,
            ),
            path(
                "change-item/",
                self.admin_site.admin_view(self.change_item_view_class.as_view()),
                name="%s_%s_change_item" % info,
            ),
            path(
                "sort-items/",
                self.admin_site.admin_view(self.sort_items_view_class.as_view()),
                name="%s_%s_sort_items" % info,
            ),
        ]
        return urlpatterns


@admin.register(Collection)
class CollectionAdmin(CollectionAdminBase):
    pass
