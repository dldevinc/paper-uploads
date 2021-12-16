from django.contrib.admin import site
from django.contrib.admin.sites import NotRegistered
from django.urls import reverse_lazy

from ...conf import settings
from ...helpers import iterate_parent_models
from .base import FileResourceWidgetBase
from .mixins import DisplayFileLimitationsMixin


class CollectionWidget(DisplayFileLimitationsMixin, FileResourceWidgetBase):
    template_name = "paper_uploads/widgets/collection.html"

    class Media:
        css = {
            "all": [
                "paper_uploads/dist/widget.css"
            ]
        }
        js = [
            "paper_uploads/dist/widget.js",
        ]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        instance = context["instance"]
        item_count = instance.get_items().count() if instance is not None else 0

        context.update(
            {
                "collection_cls": self.model,
                "item_range": range(item_count),
                "preview_width": settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                "preview_height": settings.COLLECTION_ITEM_PREVIEW_HEIGHT,
            }
        )

        for model_class in iterate_parent_models(self.model):
            if site.is_registered(model_class):
                context.update(self.get_extra_context(model_class))
                break
        else:
            raise NotRegistered("The model %s is not registered." % self.model.__name__)

        return context

    def get_instance(self, value):
        return self.model._base_manager.prefetch_related("items").get(pk=value)

    def get_extra_context(self, model):
        info = model._meta.app_label, model._meta.model_name
        return {
            "create_collection_url": reverse_lazy("admin:%s_%s_create" % info),
            "delete_collection_url": reverse_lazy("admin:%s_%s_delete" % info),
            "upload_item_url": reverse_lazy("admin:%s_%s_upload_item" % info),
            "change_item_url": reverse_lazy("admin:%s_%s_change_item" % info),
            "delete_item_url": reverse_lazy("admin:%s_%s_delete_item" % info),
            "sort_items_url": reverse_lazy("admin:%s_%s_sort_items" % info),
        }
