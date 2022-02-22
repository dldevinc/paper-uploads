# Generated by Django 4.0.2 on 2022-02-09 09:33

from django.db import migrations
import django.db.models.deletion
import paper_uploads.models.fields.image


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0001_squashed_0009_alter_collectionitembase_polymorphic_ctype_and_more'),
        ('standard_fields', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='image_group',
            field=paper_uploads.models.fields.image.ImageField(blank=True, on_delete=django.db.models.deletion.SET_NULL, storage=None, to='paper_uploads.uploadedimage', upload_to='', verbose_name='image group'),
        ),
    ]
