from django.contrib import admin

from paper_uploads.admin.collection import CollectionAdminBase

from . import views
from .models import Page, CustomCollection


@admin.register(CustomCollection)
class CustomCollectionAdmin(CollectionAdminBase):
    create_collection_view_class = views.CreateCustomCollectionView


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    pass
