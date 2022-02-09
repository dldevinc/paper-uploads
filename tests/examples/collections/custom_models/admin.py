from django.contrib import admin

from paper_uploads.admin.collection import CollectionAdminBase

from . import views
from .models import CustomCollection, Page


@admin.register(CustomCollection)
class CustomCollectionAdmin(CollectionAdminBase):
    upload_item_view_class = views.UploadCustomCollectionItemView


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    pass
