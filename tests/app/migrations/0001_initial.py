# Generated by Django 3.0.8 on 2020-07-29 18:00

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import paper_uploads.models.base
import paper_uploads.models.fields.file
import paper_uploads.models.fields.image


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('paper_uploads', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DummyFileFieldResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('content_hash', models.CharField(editable=False, help_text='hash of the contents of a file', max_length=64, verbose_name='content hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('file', models.FileField(upload_to='file_field', verbose_name='file')),
            ],
            options={
                'abstract': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='DummyFileResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('content_hash', models.CharField(editable=False, help_text='hash of the contents of a file', max_length=64, verbose_name='content hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
            ],
            options={
                'abstract': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='DummyHashableResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('content_hash', models.CharField(editable=False, help_text='hash of the contents of a file', max_length=64, verbose_name='content hash')),
            ],
            options={
                'abstract': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='DummyImageFieldResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('content_hash', models.CharField(editable=False, help_text='hash of the contents of a file', max_length=64, verbose_name='content hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('title', models.CharField(blank=True, help_text='The title is being used as a tooltip when the user hovers the mouse over the image', max_length=255, verbose_name='title')),
                ('description', models.CharField(blank=True, help_text='This text will be used by screen readers, search engines, or when the image cannot be loaded', max_length=255, verbose_name='description')),
                ('width', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='width')),
                ('height', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='height')),
                ('cropregion', models.CharField(blank=True, editable=False, max_length=24, verbose_name='crop region')),
                ('image', models.FileField(upload_to='image_field', verbose_name='file')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DummyReadonlyFileProxyResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('content_hash', models.CharField(editable=False, help_text='hash of the contents of a file', max_length=64, verbose_name='content hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('file', models.FileField(upload_to='readonly_file', verbose_name='file')),
            ],
            options={
                'abstract': False,
                'default_permissions': (),
            },
            bases=(paper_uploads.models.base.ReadonlyFileProxyMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DummyResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
            ],
            options={
                'abstract': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='DummyReverseFieldResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('content_hash', models.CharField(editable=False, help_text='hash of the contents of a file', max_length=64, verbose_name='content hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('owner_app_label', models.CharField(editable=False, max_length=100)),
                ('owner_model_name', models.CharField(editable=False, max_length=100)),
                ('owner_fieldname', models.CharField(editable=False, max_length=255)),
                ('file', models.FileField(upload_to='reverse_file', verbose_name='file')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DummyVersatileImageResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('content_hash', models.CharField(editable=False, help_text='hash of the contents of a file', max_length=64, verbose_name='content hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('title', models.CharField(blank=True, help_text='The title is being used as a tooltip when the user hovers the mouse over the image', max_length=255, verbose_name='title')),
                ('description', models.CharField(blank=True, help_text='This text will be used by screen readers, search engines, or when the image cannot be loaded', max_length=255, verbose_name='description')),
                ('width', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='width')),
                ('height', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='height')),
                ('cropregion', models.CharField(blank=True, editable=False, max_length=24, verbose_name='crop region')),
                ('file', models.FileField(upload_to='versatile_image', verbose_name='file')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImageExample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', paper_uploads.models.fields.image.ImageField(on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads.UploadedImage', verbose_name='image')),
            ],
        ),
        migrations.CreateModel(
            name='FileExample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', paper_uploads.models.fields.file.FileField(on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads.UploadedFile', verbose_name='file')),
            ],
        ),
    ]
