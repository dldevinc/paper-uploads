from django.db import migrations, transaction


class RenameFileField(migrations.RunPython):
    def __init__(self, app_label, model_name, old_name, new_name):
        self.app_label = app_label
        self.model_name = model_name
        self.old_name = old_name
        self.new_name = new_name
        super().__init__(self.rename_forward, self.rename_backward)

    def _rename(self, apps, schema_editor, old_name, new_name):
        from ..models.fields.base import FileResourceFieldBase

        db = schema_editor.connection.alias
        state_model = apps.get_model(self.app_label, self.model_name)
        for field in state_model._meta.fields:
            if field.name != self.new_name:
                continue

            if isinstance(field, FileResourceFieldBase):
                with transaction.atomic(using=db):
                    field.related_model.objects.db_manager(db).filter(
                        owner_app_label=self.app_label,
                        owner_model_name=self.model_name,
                        owner_fieldname=old_name,
                    ).update(owner_fieldname=new_name)

    def rename_forward(self, apps, schema_editor):
        self._rename(apps, schema_editor, self.old_name, self.new_name)

    def rename_backward(self, apps, schema_editor):
        self._rename(apps, schema_editor, self.new_name, self.old_name)


class RenameFileModel(migrations.RunPython):
    def __init__(self, app_label, old_name, new_name):
        self.app_label = app_label
        self.old_name = old_name
        self.new_name = new_name
        super().__init__(self.rename_forward, self.rename_backward)

    def _rename(self, apps, schema_editor, old_name, new_name, backward=False):
        from ..models.fields.base import FileResourceFieldBase

        old_name = old_name.lower()
        new_name = new_name.lower()
        db = schema_editor.connection.alias
        state_model = apps.get_model(self.app_label, old_name if backward else new_name)
        for field in state_model._meta.fields:
            if isinstance(field, FileResourceFieldBase):
                with transaction.atomic(using=db):
                    field.related_model.objects.db_manager(db).filter(
                        owner_app_label=self.app_label,
                        owner_model_name=old_name,
                        owner_fieldname=field.name,
                    ).update(owner_model_name=new_name)

    def rename_forward(self, apps, schema_editor):
        self._rename(apps, schema_editor, self.old_name, self.new_name)

    def rename_backward(self, apps, schema_editor):
        self._rename(apps, schema_editor, self.new_name, self.old_name, backward=True)


def inject_rename_filefield_operations(plan=None, **kwargs):
    if plan is None:
        return

    for migration, backward in plan:
        inserts = []
        for index, operation in enumerate(migration.operations):
            if isinstance(operation, migrations.RenameField):
                operation = RenameFileField(
                    migration.app_label,
                    operation.model_name,
                    operation.old_name_lower,
                    operation.new_name_lower,
                )
                inserts.append((index + 1, operation))
            elif isinstance(operation, migrations.RenameModel):
                operation = RenameFileModel(
                    migration.app_label,
                    operation.old_name,
                    operation.new_name,
                )
                inserts.append((index + 1, operation))

        for inserted, (index, operation) in enumerate(inserts):
            migration.operations.insert(inserted + index, operation)
