from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.cloudinary.custom_storage"
    label = "custom_cloudinary_storage"
    verbose_name = _("Standard")
