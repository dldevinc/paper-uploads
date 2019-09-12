from django.contrib import admin
from paper_admin.admin.sortable import SortableAdminMixin
from .models import Page, Document


@admin.register(Page)
class PageAdmin(SortableAdminMixin, admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'header', 'file', 'image', 'image_ext', 'files', 'gallery',
            ),
        }),
    )
    sortable = 'order'
    search_fields = ['header']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'title', 'image', 'files'
            ),
        }),
    )
