from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.collections.proxy_models"
    label = "proxy_models_collections"
    verbose_name = _("Proxy models")
