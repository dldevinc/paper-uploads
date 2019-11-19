# Generated by Django 2.2.6 on 2019-11-06 05:17

import cloudinary.models
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import django.utils.timezone
import paper_uploads.cloudinary.models.base


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0018_auto_20191102_0731'),
        ('paper_uploads_cloudinary', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudinaryFileItem',
            fields=[
                ('collectionresourceitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='paper_uploads.CollectionResourceItem')),
                ('name', models.CharField(editable=False, max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('hash', models.CharField(editable=False, help_text='SHA-1 checksum of a resource', max_length=40, verbose_name='hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('preview_url', models.CharField(blank=True, editable=False, max_length=255, verbose_name='preview URL')),
                ('file', cloudinary.models.CloudinaryField(max_length=255, verbose_name='file')),
                ('display_name', models.CharField(blank=True, max_length=255, verbose_name='display name')),
            ],
            options={
                'verbose_name': 'File item',
                'verbose_name_plural': 'File items',
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=(paper_uploads.cloudinary.models.base.ReadonlyCloudinaryFileProxyMixin, 'paper_uploads.collectionresourceitem', models.Model),
        ),
        migrations.CreateModel(
            name='CloudinaryImageItem',
            fields=[
                ('collectionresourceitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='paper_uploads.CollectionResourceItem')),
                ('name', models.CharField(editable=False, max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('hash', models.CharField(editable=False, help_text='SHA-1 checksum of a resource', max_length=40, verbose_name='hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('title', models.CharField(blank=True, help_text='The title is being used as a tooltip when the user hovers the mouse over the image', max_length=255, verbose_name='title')),
                ('description', models.CharField(blank=True, help_text='This text will be used by screen readers, search engines, or when the image cannot be loaded', max_length=255, verbose_name='description')),
                ('width', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='width')),
                ('height', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='height')),
                ('cropregion', models.CharField(blank=True, editable=False, max_length=24, verbose_name='crop region')),
                ('file', cloudinary.models.CloudinaryField(max_length=255, verbose_name='file')),
            ],
            options={
                'verbose_name': 'Image item',
                'verbose_name_plural': 'Image items',
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=(paper_uploads.cloudinary.models.base.ReadonlyCloudinaryFileProxyMixin, 'paper_uploads.collectionresourceitem', models.Model),
        ),
        migrations.CreateModel(
            name='CloudinaryMediaItem',
            fields=[
                ('collectionresourceitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='paper_uploads.CollectionResourceItem')),
                ('name', models.CharField(editable=False, max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('hash', models.CharField(editable=False, help_text='SHA-1 checksum of a resource', max_length=40, verbose_name='hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('preview_url', models.CharField(blank=True, editable=False, max_length=255, verbose_name='preview URL')),
                ('file', cloudinary.models.CloudinaryField(max_length=255, verbose_name='file')),
                ('display_name', models.CharField(blank=True, max_length=255, verbose_name='display name')),
            ],
            options={
                'verbose_name': 'Media item',
                'verbose_name_plural': 'Media items',
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=(paper_uploads.cloudinary.models.base.ReadonlyCloudinaryFileProxyMixin, 'paper_uploads.collectionresourceitem', models.Model),
        ),
        migrations.CreateModel(
            name='CloudinaryCollection',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('paper_uploads.collection',),
            managers=[
                ('default_mgr', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='CloudinaryImageCollection',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('paper_uploads.collection',),
            managers=[
                ('default_mgr', django.db.models.manager.Manager()),
            ],
        ),
    ]
