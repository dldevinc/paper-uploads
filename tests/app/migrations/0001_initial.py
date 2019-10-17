# Generated by Django 2.2.5 on 2019-09-27 13:54

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import paper_uploads.models.fields.collection
import paper_uploads.models.fields.file
import paper_uploads.models.fields.image


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('paper_uploads', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageFilesGallery',
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
            name='PageGallery',
            fields=[
            ],
            options={
                'proxy': True,
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
                ('header', models.CharField(max_length=255, verbose_name='header')),
                ('order', models.PositiveIntegerField(default=0, editable=False, verbose_name='order')),
                ('file', paper_uploads.models.fields.file.FileField(blank=True, on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads.UploadedFile', verbose_name='simple file')),
                ('files', paper_uploads.models.fields.collection.CollectionField(on_delete=django.db.models.deletion.SET_NULL, to='app.PageFilesGallery', verbose_name='file gallery')),
                ('gallery', paper_uploads.models.fields.collection.CollectionField(on_delete=django.db.models.deletion.SET_NULL, to='app.PageGallery', verbose_name='image gallery')),
                ('image', paper_uploads.models.fields.image.ImageField(blank=True, on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads.UploadedImage', verbose_name='simple image')),
                ('image_ext', paper_uploads.models.fields.image.ImageField(blank=True, on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads.UploadedImage', verbose_name='image with variations')),
            ],
            options={
                'verbose_name': 'page',
                'verbose_name_plural': 'pages',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('files', paper_uploads.models.fields.collection.CollectionField(on_delete=django.db.models.deletion.SET_NULL, to='app.PageFilesGallery', verbose_name='files')),
                ('image', paper_uploads.models.fields.image.ImageField(blank=True, on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads.UploadedImage', verbose_name='simple image')),
            ],
            options={
                'verbose_name': 'document',
                'verbose_name_plural': 'documents',
            },
        ),
    ]