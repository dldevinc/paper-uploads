# Generated by Django 2.2.5 on 2019-09-27 06:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('paper_uploads', '0015_auto_20190927_0624'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='GalleryImageItem',
            new_name='ImageItem',
        ),
    ]
