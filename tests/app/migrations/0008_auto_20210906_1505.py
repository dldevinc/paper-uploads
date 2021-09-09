# Generated by Django 3.2.6 on 2021-09-06 15:05

from django.db import migrations
import django.db.models.deletion
import paper_uploads.models.fields.file


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0003_auto_20210906_1505'),
        ('app', '0007_cloudinaryimageexample_image_public'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUploadedFile',
            fields=[
            ],
            options={
                'proxy': True,
                'default_permissions': (),
                'indexes': [],
                'constraints': [],
            },
            bases=('paper_uploads.uploadedfile',),
        ),
        migrations.AddField(
            model_name='filefieldobject',
            name='file_custom',
            field=paper_uploads.models.fields.file.FileField(blank=True, on_delete=django.db.models.deletion.SET_NULL, to='app.customuploadedfile', verbose_name='custom file'),
        ),
    ]
