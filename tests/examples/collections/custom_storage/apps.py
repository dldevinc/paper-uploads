from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.collections.custom_storage"
    label = "custom_storage_collections"
    verbose_name = _("Custom storage")
