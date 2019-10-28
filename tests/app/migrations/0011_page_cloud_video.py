# Generated by Django 2.2.6 on 2019-10-25 04:52

from django.db import migrations
import django.db.models.deletion
import paper_uploads.cloudinary.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads_cloudinary', '0003_auto_20191025_0452'),
        ('app', '0010_auto_20191025_0447'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='cloud_video',
            field=paper_uploads.cloudinary.models.fields.CloudinaryMediaField(blank=True, on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads_cloudinary.CloudinaryMedia', verbose_name='video'),
        ),
    ]
