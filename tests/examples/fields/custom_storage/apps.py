from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.fields.custom_storage"
    label = "custom_storage_fields"
    verbose_name = _("Custom storage")
