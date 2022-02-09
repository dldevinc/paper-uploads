# Generated by Django 4.0.2 on 2022-02-09 05:39

from django.db import migrations
import django.db.models.deletion
import paper_uploads.cloudinary.models.fields.file
import paper_uploads.models.fields.base
import paper_uploads.validators


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads_cloudinary', '0005_auto_20211116_0840'),
        ('app', '0027_auto_20211208_1228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cloudinaryfileexample',
            name='file_size',
            field=paper_uploads.cloudinary.models.fields.file.CloudinaryFileField(blank=True, help_text='Maximum file size is 16Kb', on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads_cloudinary.cloudinaryfile', upload_to='', validators=[paper_uploads.validators.MaxSizeValidator('16kb')], verbose_name='Size'),
        ),
        migrations.AlterField(
            model_name='dummyfilefieldresource',
            name='file',
            field=paper_uploads.models.fields.base.DynamicStorageFileField(verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='dummyimagefieldresource',
            name='image',
            field=paper_uploads.models.fields.base.DynamicStorageFileField(verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='dummyversatileimageresource',
            name='file',
            field=paper_uploads.models.fields.base.DynamicStorageFileField(verbose_name='file'),
        ),
    ]