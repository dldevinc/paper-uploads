# Generated by Django 2.2.5 on 2019-09-27 06:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('paper_uploads', '0014_auto_20190927_0623'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='GallerySVGItem',
            new_name='SVGItem',
        ),
    ]
