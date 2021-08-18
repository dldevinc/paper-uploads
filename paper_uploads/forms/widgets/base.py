from django.contrib.contenttypes.models import ContentType
from django.forms import widgets
from django.utils.functional import cached_property


class FileWidgetBase(widgets.Widget):
    owner_app_label = None
    owner_model_name = None
    owner_fieldname = None

    @cached_property
    def model(self):
        return self.choices.queryset.model  # noqa: F821

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update(
            {
                "content_type": ContentType.objects.get_for_model(
                    self.model, for_concrete_model=False
                ),
                "owner_app_label": self.owner_app_label,
                "owner_model_name": self.owner_model_name,
                "owner_fieldname": self.owner_fieldname,
                "instance": self.get_instance(value) if value else None,
            }
        )
        return context

    def get_instance(self, value):
        return self.model._base_manager.get(pk=value)
