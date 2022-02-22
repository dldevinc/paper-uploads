from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.collections.custom_models"
    label = "custom_models_collections"
    verbose_name = _("Custom models")
