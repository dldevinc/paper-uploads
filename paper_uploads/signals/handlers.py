from django.apps import apps as global_apps
from django.db import DEFAULT_DB_ALIAS, migrations, transaction
from django.db.migrations.operations.base import Operation
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.timezone import now

from .. import exceptions
from ..models import CollectionItemBase
from ..models.fields.base import ResourceFieldBase
from .classes import ExtendableMigration


@receiver(post_delete, sender=CollectionItemBase)
def on_delete_collection_item(sender, instance, **kwargs):
    """
    Обновление поля `modified_at` коллекции при удалении элемента,
    чтобы метод `get_last_modified()` возвращал корректные данные.
    """
    if instance.collection_id and instance.collection_content_type_id:
        try:
            collection_cls = instance.get_collection_class()
        except exceptions.CollectionModelNotFoundError:
            return

        collection_cls.objects.filter(
            pk=instance.collection_id
        ).update(
            modified_at=now()
        )


def inject_operations(
    plan=None, apps=global_apps, using=DEFAULT_DB_ALIAS, **kwargs
):
    if plan is None:
        return

    for migration, backward in plan:
        if migration.name == "0001_initial":
            continue

        PaperMigration(
            migration=migration,
            backward=backward,
            apps=apps,
            using=using
        ).iterate()


class PaperMigration(ExtendableMigration):
    def process(self, operation: Operation, **kwargs):
        apps = kwargs["apps"]
        if isinstance(operation, migrations.RenameField):
            self.insert_after(
                RenameOwnerField(
                    self.migration.app_label,
                    operation.model_name,
                    operation.old_name,
                    operation.new_name,
                )
            )
        elif isinstance(operation, migrations.RenameModel):
            self.insert_after(
                RenameOwnerModel(
                    self.migration.app_label,
                    operation.old_name_lower,
                    operation.new_name_lower,
                )
            )


class RenameOwnerField(migrations.RunPython):
    """
    При переименовании поля, ссылающегося на ресурс, необходимо исправить
    значение owner_fieldname во всех связанных экземплярах.
    """

    def __init__(self, app_label, model_name, old_name, new_name):
        self.app_label = app_label
        self.model_name = model_name
        self.old_name = old_name
        self.new_name = new_name
        super().__init__(self.forward, self.backward)

    def forward(self, apps, schema_editor):
        self._rename(apps, schema_editor, self.old_name, self.new_name)

    def backward(self, apps, schema_editor):
        self._rename(apps, schema_editor, self.new_name, self.old_name)

    def _rename(self, apps, schema_editor, old_name, new_name):
        using = schema_editor.connection.alias
        model = apps.get_model(self.app_label, self.model_name)

        # Текущая миграция выполняется после миграции переименования,
        # поэтому целевое поле уже имеет новое имя.
        field = model._meta.get_field(new_name)

        if isinstance(field, ResourceFieldBase):
            with transaction.atomic(using=using):
                field.related_model._base_manager.db_manager(using).filter(
                    owner_app_label=self.app_label,
                    owner_model_name=self.model_name,
                    owner_fieldname=old_name,
                ).update(
                    owner_fieldname=new_name
                )


class DeleteOwnerModel(migrations.RunPython):
    """
    При переименовании модели, в которой есть поля, ссылающиеся на ресурсы,
    необходимо исправить значение owner_model_name во всех связанных экземплярах.
    """

    def __init__(self, app_label, old_name, new_name):
        self.app_label = app_label
        self.old_name = old_name
        self.new_name = new_name
        super().__init__(self.forward, self.backward)

    def forward(self, apps, schema_editor):
        self._rename(apps, schema_editor, self.old_name, self.new_name)

    def backward(self, apps, schema_editor):
        self._rename(apps, schema_editor, self.new_name, self.old_name)

    def _rename(self, apps, schema_editor, old_name, new_name):
        using = schema_editor.connection.alias

        # Текущая миграция выполняется после миграции переименования,
        # поэтому модель уже имеет новое имя.
        model = apps.get_model(self.app_label, new_name)

        with transaction.atomic(using=using):
            for field in model._meta.fields:
                if isinstance(field, ResourceFieldBase):
                    field.related_model._base_manager.db_manager(using).filter(
                        owner_app_label=self.app_label,
                        owner_model_name=old_name,
                        owner_fieldname=field.name,
                    ).update(
                        owner_model_name=new_name
                    )
