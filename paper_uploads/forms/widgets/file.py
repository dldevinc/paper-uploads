from django.contrib.admin import site
from django.contrib.admin.sites import NotRegistered
from django.urls import reverse_lazy

from ...helpers import iterate_parent_models
from .base import FileResourceWidgetBase
from .mixins import DisplayFileLimitationsMixin


class FileWidget(DisplayFileLimitationsMixin, FileResourceWidgetBase):
    template_name = "paper_uploads/widgets/file.html"

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

        for model_class in iterate_parent_models(self.model):
            if site.is_registered(model_class):
                context.update(self.get_extra_context(model_class))
                break
        else:
            raise NotRegistered("The model %s is not registered." % self.model.__name__)

        return context

    def get_extra_context(self, model):
        info = model._meta.app_label, model._meta.model_name
        return {
            "upload_url": reverse_lazy("admin:%s_%s_upload" % info),
            "change_url": reverse_lazy("admin:%s_%s_change" % info),
            "delete_url": reverse_lazy("admin:%s_%s_delete" % info),
        }
