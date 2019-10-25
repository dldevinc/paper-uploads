# Generated by Django 2.2.6 on 2019-10-25 04:52

import cloudinary.models
from django.db import migrations, models
import django.utils.timezone
import paper_uploads.cloudinary.container
import paper_uploads.models.base
import paper_uploads.models.containers.base


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads_cloudinary', '0002_cloudinaryimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudinaryVideo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, max_length=255, verbose_name='file name')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='file extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='file size')),
                ('hash', models.CharField(editable=False, help_text='SHA-1 hash of the file contents', max_length=40, verbose_name='file hash')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('owner_app_label', models.CharField(editable=False, max_length=100)),
                ('owner_model_name', models.CharField(editable=False, max_length=100)),
                ('owner_fieldname', models.CharField(editable=False, max_length=255)),
                ('file', cloudinary.models.CloudinaryField(max_length=255, verbose_name='file')),
                ('display_name', models.CharField(blank=True, max_length=255, verbose_name='display name')),
            ],
            options={
                'verbose_name': 'video',
                'verbose_name_plural': 'videos',
                'abstract': False,
                'default_permissions': (),
            },
            bases=(paper_uploads.cloudinary.container.CloudinaryContainerMixin, paper_uploads.models.base.ProxyFileAttributesMixin, paper_uploads.models.containers.base.ContainerMixinBase, models.Model),
        ),
        migrations.AlterModelOptions(
            name='cloudinaryimage',
            options={'default_permissions': (), 'verbose_name': 'image', 'verbose_name_plural': 'images'},
        ),
    ]
