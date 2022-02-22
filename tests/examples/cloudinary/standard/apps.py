from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "examples.cloudinary.standard"
    label = "standard_cloudinary_fields"
    verbose_name = _("Standard")
