from django import forms
from django.contrib.admin import site
from django.contrib.admin.sites import NotRegistered
from django.urls import reverse_lazy

from ...conf import settings
from .base import FileResourceWidgetBase
from .mixins import DisplayFileLimitationsMixin


class CollectionWidget(DisplayFileLimitationsMixin, FileResourceWidgetBase):
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

        instance = context["instance"]
        item_count = instance.get_items().count() if instance is not None else 0

        context.update(
            {
                "collection_cls": self.model,
                "item_range": range(item_count),
                "preview_width": settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                "preview_height": settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
            }
        )

        # proxy-models will use same URLs, except they have their own ModelAdmin
        for model_class in (self.model, self.model._meta.concrete_model):
            if site.is_registered(model_class):
                info = model_class._meta.app_label, model_class._meta.model_name
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
                break
        else:
            raise NotRegistered("The model %s is not registered." % self.model.__name__)

        return context

    def get_instance(self, value):
        return self.model._base_manager.prefetch_related("items").get(pk=value)
