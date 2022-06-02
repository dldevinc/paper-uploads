from django.apps import AppConfig
from django.db.models.signals import pre_migrate
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = "paper_uploads"
    verbose_name = _("Uploaded Files")

    def ready(self):
        from .signals import handlers

        pre_migrate.connect(handlers.inject_operations, sender=self)
