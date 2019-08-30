from django.forms import widgets
from django.contrib.contenttypes.models import ContentType


class FileWidgetBase(widgets.Widget):
    def get_context(self, name, value, attrs):
        model_class = self.choices.queryset.model
        context = super().get_context(name, value, attrs)
        context.update({
            'content_type': ContentType.objects.get_for_model(model_class, for_concrete_model=False),
            'instance': self.get_instance(value)
        })
        return context

    def get_instance(self, value):
        if value:
            model_class = self.choices.queryset.model
            return model_class._meta.base_manager.get(pk=value)
