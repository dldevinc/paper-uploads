# Generated by Django 3.2.6 on 2021-09-09 07:55

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import paper_uploads.models.fields.collection


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0003_auto_20210906_1505'),
        ('app', '0010_isolatedfilecollection_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomImageItem',
            fields=[
                ('imageitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='paper_uploads.imageitem')),
            ],
            options={
                'default_permissions': (),
            },
            bases=('paper_uploads.imageitem',),
        ),
        migrations.CreateModel(
            name='CustomGallery',
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
        migrations.AddField(
            model_name='collectionfieldobject',
            name='custom_collection',
            field=paper_uploads.models.fields.collection.CollectionField(on_delete=django.db.models.deletion.SET_NULL, to='app.customgallery'),
        ),
    ]
