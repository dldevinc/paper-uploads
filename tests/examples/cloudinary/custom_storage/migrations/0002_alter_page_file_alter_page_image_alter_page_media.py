# Generated by Django 4.0.1 on 2022-02-14 14:50

from django.db import migrations
import django.db.models.deletion
import paper_uploads.cloudinary.models.fields.file
import paper_uploads.cloudinary.models.fields.image
import paper_uploads.cloudinary.models.fields.media


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads_cloudinary', '0005_auto_20211116_0840'),
        ('custom_cloudinary_storage', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='file',
            field=paper_uploads.cloudinary.models.fields.file.CloudinaryFileField(blank=True, on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads_cloudinary.cloudinaryfile', upload_to='custom-files/%Y', verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='page',
            name='image',
            field=paper_uploads.cloudinary.models.fields.image.CloudinaryImageField(blank=True, on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads_cloudinary.cloudinaryimage', upload_to='custom-images/%Y', verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='page',
            name='media',
            field=paper_uploads.cloudinary.models.fields.media.CloudinaryMediaField(blank=True, on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads_cloudinary.cloudinarymedia', upload_to='custom-media/%Y', verbose_name='media'),
        ),
    ]