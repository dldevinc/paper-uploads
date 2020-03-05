from django.apps import AppConfig, apps
from django.contrib.admin.sites import site
from django.db.models.signals import pre_migrate
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = 'paper_uploads'
    verbose_name = _('Uploaded Files')

    def ready(self):
        from .signals import handlers
        from .models import CollectionBase
        from .admin import CollectionAdminBase

        pre_migrate.connect(handlers.inject_rename_filefield_operations, sender=self)

        # автоматическая регистрация моделей галерей в админке
        for model in apps.get_models():
            if issubclass(model, CollectionBase) and not site.is_registered(model):
                site.register(model, CollectionAdminBase)
