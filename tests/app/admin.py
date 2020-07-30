from django.contrib import admin

from .models import Page, Document


class DocumentInline(admin.StackedInline):
    model = Document
    extra = 0


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'header', 'file',
            ),
        }),
    )
    inlines = (DocumentInline, )
