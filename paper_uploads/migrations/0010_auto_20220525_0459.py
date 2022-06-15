# Generated by Django 4.0.4 on 2022-05-24 12:26

from django.db import migrations


def forward_func(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Collection = apps.get_model("paper_uploads", "Collection")
    CollectionItemBase = apps.get_model("paper_uploads", "CollectionItemBase")
    db_alias = schema_editor.connection.alias

    collection_updates = []
    for collection in Collection._default_manager.using(db_alias).all().iterator():
        collection_class = apps.get_model(
            collection.collection_content_type.app_label,
            collection.collection_content_type.model
        )
        concrete_collection_class = collection_class._meta.concrete_model
        concrete_content_type = ContentType._default_manager.get_for_model(concrete_collection_class)
        collection.concrete_collection_content_type_id = concrete_content_type.id
        collection_updates.append(collection)

    Collection._default_manager.bulk_update(collection_updates, ["concrete_collection_content_type_id"])

    item_updates = []
    for item in CollectionItemBase._default_manager.using(db_alias).all().iterator():
        collection_class = apps.get_model(
            item.collection_content_type.app_label,
            item.collection_content_type.model
        )
        concrete_collection_class = collection_class._meta.concrete_model
        concrete_content_type = ContentType._default_manager.get_for_model(concrete_collection_class)
        item.concrete_collection_content_type_id = concrete_content_type.id
        item_updates.append(item)

    CollectionItemBase._default_manager.bulk_update(item_updates, ["concrete_collection_content_type_id"])


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('paper_uploads', '0009_collection_concrete_collection_content_type_and_more'),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
    ]