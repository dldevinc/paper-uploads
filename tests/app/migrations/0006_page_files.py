# Generated by Django 2.2.4 on 2019-08-30 08:16

from django.db import migrations
import django.db.models.deletion
import paper_uploads.models.fields.gallery


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20190830_0815'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='files',
            field=paper_uploads.models.fields.gallery.CollectionField(on_delete=django.db.models.deletion.SET_NULL, to='app.PageFilesGallery', verbose_name='file gallery'),
        ),
    ]
