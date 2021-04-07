from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    label = "paper_uploads_cloudinary"
    name = "paper_uploads.cloudinary"
    verbose_name = _("Uploaded Files")
