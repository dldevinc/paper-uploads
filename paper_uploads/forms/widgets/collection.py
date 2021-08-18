from django import forms
from django.urls import reverse_lazy

from ...conf import settings
from .base import FileWidgetBase
from .mixins import FileUploaderWidgetMixin


class CollectionWidget(FileUploaderWidgetMixin, FileWidgetBase):
    template_name = "paper_uploads/collection_widget.html"

    @property
    def media(self):
        return forms.Media(
            js=[
                "paper_uploads/dist/widget.js",
            ],
            css={
                "screen": [
                    "paper_uploads/dist/widget.css",
                ],
            },
        )

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update(
            {
                "collection_cls": self.model,
                "preview_width": settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                "preview_height": settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            }
        )

        # urls
        info = self.model._meta.app_label, self.model._meta.model_name
        context.update(
            {
                "create_collection_url": reverse_lazy("admin:%s_%s_create" % info),
                "delete_collection_url": reverse_lazy("admin:%s_%s_delete" % info),
                "upload_item_url": reverse_lazy("admin:%s_%s_upload_item" % info),
                "change_item_url": reverse_lazy("admin:%s_%s_change_item" % info),
                "delete_item_url": reverse_lazy("admin:%s_%s_delete_item" % info),
                "sort_items_url": reverse_lazy("admin:%s_%s_sort_items" % info),
            }
        )
        return context

    def get_instance(self, value):
        return self.model._base_manager.prefetch_related("items").get(pk=value)
