# Generated by Django 4.0.2 on 2022-02-09 09:31

from django.db import migrations, models
import django.db.models.deletion
import paper_uploads.models.fields.file
import paper_uploads.models.fields.image
import paper_uploads.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('paper_uploads', '0001_squashed_0009_alter_collectionitembase_polymorphic_ctype_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filter_ext', paper_uploads.models.fields.file.FileField(blank=True, help_text='Only `pdf`, `txt` and `doc` allowed', on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads.uploadedfile', upload_to='', validators=[paper_uploads.validators.ExtensionValidator(['.pdf', '.txt', '.doc'])], verbose_name='extension')),
                ('filter_image_ext', paper_uploads.models.fields.image.ImageField(blank=True, help_text='Only `png` and `gif` allowed', on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads.uploadedimage', upload_to='', validators=[paper_uploads.validators.ExtensionValidator(['.gif', '.png'])], verbose_name='extension (image)')),
                ('filter_max_size', paper_uploads.models.fields.image.ImageField(blank=True, help_text='Image should be at most 1024x768 pixels', on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads.uploadedimage', upload_to='', validators=[paper_uploads.validators.ImageMaxSizeValidator(1024, 768)], verbose_name='maximum size')),
                ('filter_mime', paper_uploads.models.fields.file.FileField(blank=True, help_text='Only `image/svg+xml` and `image/gif` allowed', on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads.uploadedfile', upload_to='', validators=[paper_uploads.validators.MimeTypeValidator(['image/svg+xml', 'image/gif'])], verbose_name='MIME type')),
                ('filter_min_size', paper_uploads.models.fields.image.ImageField(blank=True, help_text='Image should be at least 640x480 pixels', on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads.uploadedimage', upload_to='', validators=[paper_uploads.validators.ImageMinSizeValidator(640, 480)], verbose_name='minimum size')),
                ('filter_size', paper_uploads.models.fields.file.FileField(blank=True, help_text='Maximum file size is 16Kb', on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads.uploadedfile', upload_to='', validators=[paper_uploads.validators.MaxSizeValidator('16kb')], verbose_name='size')),
            ],
            options={
                'verbose_name': 'Page',
            },
        ),
    ]