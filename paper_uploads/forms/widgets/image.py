import json
from django import forms
from django.urls import reverse_lazy
from .base import FileWidgetBase


class ImageWidget(FileWidgetBase):
    template_name = 'paper_uploads/image_widget.html'

    @property
    def media(self):
        return forms.Media(
            js=[
                'paper_uploads/dist/widget.min.js',
            ],
            css={
                'screen': [
                    'paper_uploads/dist/widget.min.css',
                ],
            },
        )

    def get_context(self, name, value, attrs):
        model_class = self.choices.queryset.model

        context = super().get_context(name, value, attrs)
        context.update({
            'validation': json.dumps(model_class.get_validation()),
        })

        # urls
        info = model_class._meta.app_label, model_class._meta.model_name
        context.update({
            'upload_url': reverse_lazy('admin:%s_%s_upload' % info),
            'change_url': reverse_lazy('admin:%s_%s_change' % info),
            'delete_url': reverse_lazy('admin:%s_%s_delete' % info),
        })
        return context
