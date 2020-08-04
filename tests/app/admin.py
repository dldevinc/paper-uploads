from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import FileFieldObject, ImageFieldObject


@admin.register(FileFieldObject)
class FileFieldObjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'file', 'file_required',
            ),
        }),
        (_('Validators'), {
            'fields': (
                'file_extensions', 'file_mimetypes', 'file_size'
            ),
        }),
    )


@admin.register(ImageFieldObject)
class ImageFieldObjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'image', 'image_required',
            ),
        }),
        (_('Validators'), {
            'fields': (
                'image_extensions', 'image_mimetypes', 'image_size',
                'image_min_size', 'image_max_size'
            ),
        }),
    )
