from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.fields.proxy_models"
    label = "proxy_models_fields"
    verbose_name = _("Proxy models")
