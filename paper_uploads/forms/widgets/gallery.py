import json
from django import forms
from django.urls import reverse_lazy
from .base import FileWidgetBase
from ...conf import settings


class GalleryWidget(FileWidgetBase):
    template_name = 'paper_uploads/gallery_widget.html'
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
        gallery_cls = self.choices.queryset.model

        context = super().get_context(name, value, attrs)
        context.update({
            'owner_app_label': self.owner_app_label,
            'owner_model_name': self.owner_model_name,
            'owner_fieldname': self.owner_fieldname,
            'gallery_cls': gallery_cls,
            'preview_width': settings.GALLERY_ITEM_PREVIEW_WIDTH,
            'preview_height': settings.GALLERY_ITEM_PREVIEW_HEIGTH,
            'validation': json.dumps(gallery_cls.get_validation()),
        })

        # urls
        info = gallery_cls._meta.app_label, gallery_cls._meta.model_name
        context.update({
            'delete_gallery_url': reverse_lazy('admin:%s_%s_delete' % info),
            'upload_item_url': reverse_lazy('admin:%s_%s_upload_item' % info),
            'change_item_url': reverse_lazy('admin:%s_%s_change_item' % info),
            'delete_item_url': reverse_lazy('admin:%s_%s_delete_item' % info),
            'sort_items_url': reverse_lazy('admin:%s_%s_sort_items' % info),
        })
        return context

    def get_instance(self, value):
        if value:
            gallery_cls = self.choices.queryset.model
            return gallery_cls._meta.base_manager.prefetch_related('items').get(pk=value)
