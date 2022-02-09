from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.fields.custom_models"
    label = "custom_models_fields"
    verbose_name = _("Custom models")
