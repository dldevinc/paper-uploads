from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.fields.standard"
    label = "standard_fields"
    verbose_name = _("Standard")
