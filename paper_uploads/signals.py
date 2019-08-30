from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, Signal
from django.db import migrations, router, transaction
from .models import UploadedFileBase, GalleryImageItemBase
from .models.fields import ImageField, GalleryField

gallery_reordered = Signal(providing_args=["instance"])


def update_gallery_cover(gallery, skip_if=None):
    if gallery.cover_id in {None, skip_if}:
        type(gallery)._base_manager.filter(pk=gallery.pk).update(
            cover=gallery.get_items('image').exclude(pk=skip_if).first()
        )


@receiver(post_save)
def set_gallery_cover_on_save(sender, instance, **kwargs):
    if isinstance(instance, GalleryImageItemBase):
        if instance.gallery is not None:
            update_gallery_cover(instance.gallery)


@receiver(post_delete)
def set_gallery_cover_on_delete(sender, instance, **kwargs):
    if isinstance(instance, GalleryImageItemBase):
        if 'gallery' not in instance.__dict__:
            # fix __getattr__ recursion
            return
        if instance.gallery is not None:
            update_gallery_cover(instance.gallery, skip_if=instance.pk)


@receiver(post_delete)
def delete_uploaded_file(sender, instance, **kwargs):
    if isinstance(instance, UploadedFileBase):
        instance.post_delete_callback()


class RenameFileField(migrations.RunPython):
    def __init__(self, app_label, model_name, old_name, new_name):
        self.app_label = app_label
        self.model_name = model_name
        self.old_name = old_name
        self.new_name = new_name
        super().__init__(self.rename_forward, self.rename_backward)

    def _rename(self, apps, schema_editor, state, old_name, new_name):
        content_type_model = apps.get_model('contenttypes', 'ContentType')
        db = schema_editor.connection.alias
        state_model = state.models[self.app_label, self.model_name]

        try:
            content_type_model = content_type_model.objects.db_manager(db).get_by_natural_key(self.app_label, self.model_name)
        except content_type_model.DoesNotExist:
            pass
        else:
            for name, instance in state_model.fields:
                if name != self.new_name:
                    continue

                if not isinstance(instance, (ImageField, GalleryField)):
                    continue

                owner_app_label, owner_model_name = instance.related_model.rsplit('.', 1)
                owner_model = apps.get_model(owner_app_label, owner_model_name)
                with transaction.atomic(using=db):
                    owner_model.objects.db_manager(db).filter(
                        owner_ct=content_type_model,
                        owner_fieldname=old_name
                    ).update(
                        owner_fieldname=new_name
                    )

    def rename_forward(self, apps, schema_editor, state_model):
        self._rename(apps, schema_editor, state_model, self.old_name, self.new_name)

    def rename_backward(self, apps, schema_editor, state_model):
        self._rename(apps, schema_editor, state_model, self.new_name, self.old_name)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        from_state.clear_delayed_apps_cache()
        if router.allow_migrate(schema_editor.connection.alias, app_label, **self.hints):
            self.code(from_state.apps, schema_editor, from_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if router.allow_migrate(schema_editor.connection.alias, app_label, **self.hints):
            self.reverse_code(from_state.apps, schema_editor, from_state)


def inject_rename_filefield_operations(plan=None, **kwargs):
    if plan is None:
        return

    for migration, backward in plan:
        inserts = []
        for index, operation in enumerate(migration.operations):
            if not isinstance(operation, migrations.RenameField):
                continue

            operation = RenameFileField(
                migration.app_label, operation.model_name, operation.old_name_lower, operation.new_name_lower
            )
            inserts.append((index + 1, operation))

        for inserted, (index, operation) in enumerate(inserts):
            migration.operations.insert(inserted + index, operation)
