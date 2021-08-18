from django import forms
from django.urls import reverse_lazy

from .base import FileWidgetBase
from .mixins import FileUploaderWidgetMixin


class ImageWidget(FileUploaderWidgetMixin, FileWidgetBase):
    template_name = "paper_uploads/image_widget.html"

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

        # urls
        info = self.model._meta.app_label, self.model._meta.model_name
        context.update(
            {
                "upload_url": reverse_lazy("admin:%s_%s_upload" % info),
                "change_url": reverse_lazy("admin:%s_%s_change" % info),
                "delete_url": reverse_lazy("admin:%s_%s_delete" % info),
            }
        )
        return context
