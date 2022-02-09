from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.collections.validators"
    label = "validators_collections"
    verbose_name = _("Validators")
