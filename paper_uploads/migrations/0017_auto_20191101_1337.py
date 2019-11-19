# Generated by Django 2.2.6 on 2019-11-01 13:37

import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import paper_uploads.models.base
import paper_uploads.models.fields.base
import paper_uploads.models.fields.image


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('paper_uploads', '0016_auto_20191101_1336'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionResourceItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collection_id', models.IntegerField()),
                ('item_type', models.CharField(db_index=True, editable=False, max_length=32, verbose_name='type')),
                ('order', models.IntegerField(default=0, editable=False, verbose_name='order')),
                ('collection_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_paper_uploads.collectionresourceitem_set+', to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'item',
                'verbose_name_plural': 'items',
                'abstract': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='FileItem',
            fields=[
                ('collectionresourceitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='paper_uploads.CollectionResourceItem')),
                ('name', models.CharField(editable=False, max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('hash', models.CharField(editable=False, help_text='SHA-1 checksum of a resource', max_length=40, verbose_name='hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('preview', models.CharField(blank=True, editable=False, max_length=255, verbose_name='preview URL')),
                ('file', paper_uploads.models.fields.base.FormattedFileField(max_length=255, storage=django.core.files.storage.FileSystemStorage(), upload_to='collections/files/%Y-%m-%d', verbose_name='file')),
                ('display_name', models.CharField(blank=True, max_length=255, verbose_name='display name')),
            ],
            options={
                'verbose_name': 'File item',
                'verbose_name_plural': 'File items',
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=(paper_uploads.models.base.ReadonlyFileProxyMixin, 'paper_uploads.collectionresourceitem', models.Model),
        ),
        migrations.CreateModel(
            name='ImageItem',
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
                ('file', paper_uploads.models.fields.image.VariationalFileField(max_length=255, storage=django.core.files.storage.FileSystemStorage(), upload_to='collections/images/%Y-%m-%d', verbose_name='file')),
            ],
            options={
                'verbose_name': 'Image item',
                'verbose_name_plural': 'Image items',
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=(paper_uploads.models.base.ReadonlyFileProxyMixin, 'paper_uploads.collectionresourceitem', models.Model),
        ),
        migrations.CreateModel(
            name='SVGItem',
            fields=[
                ('collectionresourceitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='paper_uploads.CollectionResourceItem')),
                ('name', models.CharField(editable=False, max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('hash', models.CharField(editable=False, help_text='SHA-1 checksum of a resource', max_length=40, verbose_name='hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('file', paper_uploads.models.fields.base.FormattedFileField(max_length=255, storage=django.core.files.storage.FileSystemStorage(), upload_to='collections/files/%Y-%m-%d', verbose_name='file')),
                ('display_name', models.CharField(blank=True, max_length=255, verbose_name='display name')),
            ],
            options={
                'verbose_name': 'SVG item',
                'verbose_name_plural': 'SVG items',
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=(paper_uploads.models.base.ReadonlyFileProxyMixin, 'paper_uploads.collectionresourceitem', models.Model),
        ),
        migrations.DeleteModel(
            name='CollectionItemBase',
        ),
    ]
