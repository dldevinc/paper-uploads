from django import forms
from django.urls import reverse_lazy
from .base import FileWidgetBase


class ImageWidget(FileWidgetBase):
    template_name = 'paper_uploads/image_widget.html'
    owner_app_label = None
    owner_model_name = None
    owner_fieldname = None

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
        context = super().get_context(name, value, attrs)
        context['owner_app_label'] = self.owner_app_label
        context['owner_model_name'] = self.owner_model_name
        context['owner_fieldname'] = self.owner_fieldname

        # urls
        model_class = self.choices.queryset.model
        info = model_class._meta.app_label, model_class._meta.model_name
        context.update({
            'upload_url': reverse_lazy('admin:%s_%s_upload' % info),
            'change_url': reverse_lazy('admin:%s_%s_change' % info),
            'delete_url': reverse_lazy('admin:%s_%s_delete' % info),
        })
        return context
