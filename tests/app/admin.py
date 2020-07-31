from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import FileFieldObject


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
                'file_extensions',
            ),
        }),
    )
