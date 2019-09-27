from django import forms
from django.urls import reverse_lazy
from .base import FileWidgetBase
from ...conf import settings


class CollectionWidget(FileWidgetBase):
    template_name = 'paper_uploads/gallery_widget.html'

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
        context.update({
            'gallery_cls': self.model,
            'preview_width': settings.GALLERY_ITEM_PREVIEW_WIDTH,
            'preview_height': settings.GALLERY_ITEM_PREVIEW_HEIGTH,
        })

        # urls
        info = self.model._meta.app_label, self.model._meta.model_name
        context.update({
            'delete_gallery_url': reverse_lazy('admin:%s_%s_delete' % info),
            'upload_item_url': reverse_lazy('admin:%s_%s_upload_item' % info),
            'change_item_url': reverse_lazy('admin:%s_%s_change_item' % info),
            'delete_item_url': reverse_lazy('admin:%s_%s_delete_item' % info),
            'sort_items_url': reverse_lazy('admin:%s_%s_sort_items' % info),
        })
        return context

    def get_instance(self, value):
        return self.model._base_manager.prefetch_related('items').get(pk=value)
