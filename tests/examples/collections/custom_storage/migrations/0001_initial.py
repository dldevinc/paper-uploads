# Generated by Django 4.0.2 on 2022-02-09 10:41

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import paper_uploads.models.fields.collection


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('paper_uploads', '0001_squashed_0009_alter_collectionitembase_polymorphic_ctype_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MixedCollection',
            fields=[
            ],
            options={
                'proxy': True,
                'default_permissions': (),
                'indexes': [],
                'constraints': [],
            },
            bases=('paper_uploads.collection',),
            managers=[
                ('default_mgr', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='Photos',
            fields=[
            ],
            options={
                'proxy': True,
                'default_permissions': (),
                'indexes': [],
                'constraints': [],
            },
            bases=('paper_uploads.imagecollection',),
            managers=[
                ('default_mgr', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collection', paper_uploads.models.fields.collection.CollectionField(on_delete=django.db.models.deletion.SET_NULL, storage=None, to='custom_storage_collections.mixedcollection', upload_to='', verbose_name='collection')),
                ('gallery', paper_uploads.models.fields.collection.CollectionField(on_delete=django.db.models.deletion.SET_NULL, storage=None, to='custom_storage_collections.photos', upload_to='', verbose_name='gallery')),
            ],
            options={
                'verbose_name': 'Page',
            },
        ),
    ]
