from django.forms import widgets
from django.contrib.contenttypes.models import ContentType


class FileWidgetBase(widgets.Widget):
    owner_app_label = None
    owner_model_name = None
    owner_fieldname = None

    def get_context(self, name, value, attrs):
        model_class = self.choices.queryset.model
        context = super().get_context(name, value, attrs)
        context.update({
            'content_type': ContentType.objects.get_for_model(model_class, for_concrete_model=False),
            'owner_app_label': self.owner_app_label,
            'owner_model_name': self.owner_model_name,
            'owner_fieldname': self.owner_fieldname,
            'instance': self.get_instance(value)
        })
        return context

    def get_instance(self, value):
        if value:
            model_class = self.choices.queryset.model
            return model_class._meta.base_manager.get(pk=value)
