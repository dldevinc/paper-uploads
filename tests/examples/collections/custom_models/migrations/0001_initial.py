# Generated by Django 4.0.2 on 2022-02-09 14:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import django.utils.timezone
import paper_uploads.models.fields.collection
import paper_uploads.models.fields.image
import paper_uploads.models.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('paper_uploads', '0001_squashed_0009_alter_collectionitembase_polymorphic_ctype_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomCollection',
            fields=[
                ('collection_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='paper_uploads.collection')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'proxy': False,
                'default_permissions': (),
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
                ('collection', paper_uploads.models.fields.collection.CollectionField(on_delete=django.db.models.deletion.SET_NULL, storage=None, to='custom_models_collections.customcollection', upload_to='', verbose_name='collection')),
            ],
            options={
                'verbose_name': 'Page',
            },
        ),
        migrations.CreateModel(
            name='ImageItem',
            fields=[
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('basename', models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='basename')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('checksum', models.CharField(editable=False, max_length=64, verbose_name='checksum')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('title', models.CharField(blank=True, help_text='The title is being used as a tooltip when the user hovers the mouse over the image', max_length=255, verbose_name='title')),
                ('description', models.TextField(blank=True, help_text='This text will be used by screen readers, search engines, or when the image cannot be loaded', verbose_name='description')),
                ('width', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='width')),
                ('height', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='height')),
                ('cropregion', models.CharField(blank=True, editable=False, max_length=24, verbose_name='crop region')),
                ('file', paper_uploads.models.fields.image.VariationalFileField(verbose_name='file')),
                ('collectionitembase_ptr', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='+', serialize=False, to='paper_uploads.collectionitembase')),
                ('caption', models.TextField(blank=True, verbose_name='caption')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'default_permissions': (),
            },
            bases=('paper_uploads.collectionitembase', paper_uploads.models.mixins.FileFieldProxyMixin, paper_uploads.models.mixins.FileProxyMixin, models.Model),
        ),
    ]