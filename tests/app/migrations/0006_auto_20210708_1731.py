# Generated by Django 2.1.15 on 2021-07-08 17:31

from django.db import migrations, models
import django.db.models.deletion
import paper_uploads.cloudinary.models.fields.file
import paper_uploads.models.fields.file
import paper_uploads.validators


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads_cloudinary', '0002_auto_20210407_0627'),
        ('app', '0005_auto_20210407_0627'),
    ]

    operations = [
        migrations.AddField(
            model_name='cloudinaryfileexample',
            name='file_extensions',
            field=paper_uploads.cloudinary.models.fields.file.CloudinaryFileField(blank=True, help_text='Only `pdf`, `txt` and `doc` allowed', on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads_cloudinary.CloudinaryFile', validators=[paper_uploads.validators.ExtensionValidator(['.pdf', '.txt', '.doc'])], verbose_name='Extension'),
        ),
        migrations.AddField(
            model_name='cloudinaryfileexample',
            name='file_mimetypes',
            field=paper_uploads.cloudinary.models.fields.file.CloudinaryFileField(blank=True, help_text='Only `image/svg+xml` and `image/gif` allowed', on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads_cloudinary.CloudinaryFile', validators=[paper_uploads.validators.MimeTypeValidator(['image/svg+xml', 'image/gif'])], verbose_name='MimeType'),
        ),
        migrations.AddField(
            model_name='cloudinaryfileexample',
            name='file_required',
            field=paper_uploads.cloudinary.models.fields.file.CloudinaryFileField(on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads_cloudinary.CloudinaryFile', verbose_name='required file'),
        ),
        migrations.AddField(
            model_name='cloudinaryfileexample',
            name='file_size',
            field=paper_uploads.cloudinary.models.fields.file.CloudinaryFileField(blank=True, help_text='Maximum file size is 16Kb', on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads_cloudinary.CloudinaryFile', validators=[paper_uploads.validators.SizeValidator('16kb')], verbose_name='Size'),
        ),
        migrations.AddField(
            model_name='cloudinaryfileexample',
            name='name',
            field=models.CharField(default='', max_length=128, verbose_name='name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cloudinaryfileexample',
            name='file',
            field=paper_uploads.cloudinary.models.fields.file.CloudinaryFileField(blank=True, on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads_cloudinary.CloudinaryFile', verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='filefieldobject',
            name='file_mimetypes',
            field=paper_uploads.models.fields.file.FileField(blank=True, help_text='Only `image/svg+xml` and `image/gif` allowed', on_delete=django.db.models.deletion.SET_NULL, to='paper_uploads.UploadedFile', validators=[paper_uploads.validators.MimeTypeValidator(['image/svg+xml', 'image/gif'])], verbose_name='MimeType'),
        ),
    ]
