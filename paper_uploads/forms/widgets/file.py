from django import forms
from django.contrib.admin import site
from django.contrib.admin.sites import NotRegistered
from django.urls import reverse_lazy

from .base import FileResourceWidgetBase
from .mixins import DisplayFileLimitationsMixin


class FileWidget(DisplayFileLimitationsMixin, FileResourceWidgetBase):
    template_name = "paper_uploads/file_widget.html"

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

        # proxy-models will use same URLs, except they have their own ModelAdmin
        for model_class in (self.model, self.model._meta.concrete_model):
            if site.is_registered(model_class):
                info = model_class._meta.app_label, model_class._meta.model_name
                context.update(
                    {
                        "upload_url": reverse_lazy("admin:%s_%s_upload" % info),
                        "change_url": reverse_lazy("admin:%s_%s_change" % info),
                        "delete_url": reverse_lazy("admin:%s_%s_delete" % info),
                    }
                )
                break
        else:
            raise NotRegistered("The model %s is not registered." % self.model.__name__)

        return context
