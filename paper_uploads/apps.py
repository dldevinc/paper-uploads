from django.apps import apps, AppConfig
from django.contrib.admin.sites import site
from django.db.models.signals import pre_migrate
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    name = 'paper_uploads'
    verbose_name = _('Uploaded Files')

    def ready(self):
        from . import signals
        from .models import GalleryBase
        from .admin import CollectionAdminBase
        pre_migrate.connect(signals.inject_rename_filefield_operations, sender=self)

        # автоматическая регистрация моделей галерей в админке
        for model in apps.get_models():
            if issubclass(model, GalleryBase) and not site.is_registered(model):
                site.register(model, CollectionAdminBase)
