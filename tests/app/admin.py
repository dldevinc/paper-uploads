from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from paper_admin.admin.sortable import SortableAdminMixin

from .models import Document, Page


@admin.register(Page)
class PageAdmin(SortableAdminMixin, admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'header', 'file', 'image', 'image_ext', 'files', 'gallery',
            ),
        }),
        (_('Validators'), {
            'fields': (
                'ext_file', 'mime_file', 'size_file', 'min_image', 'max_image',
                'png_gallery'
            ),
        }),
        (_('Cloudinary'), {
            'fields': (
                'cloud_file', 'cloud_video', 'cloud_image',
                'cloud_files', 'cloud_gallery',
            )
        })
    )
    sortable = 'order'
    search_fields = ['header']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'page', 'title', 'image', 'files'
            ),
        }),
    )
    autocomplete_fields = ['page']
