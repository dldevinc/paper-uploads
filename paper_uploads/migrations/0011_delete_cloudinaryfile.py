# Generated by Django 2.2.6 on 2019-10-24 10:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0010_cloudinaryfile'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CloudinaryFile',
        ),
    ]
