# Generated by Django 3.1.8 on 2021-04-07 06:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='collection',
            options={'default_manager_name': 'default_mgr', 'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='fileitem',
            options={'base_manager_name': 'objects', 'default_permissions': (), 'verbose_name': 'File item', 'verbose_name_plural': 'File items'},
        ),
        migrations.AlterModelOptions(
            name='imagecollection',
            options={'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='imageitem',
            options={'base_manager_name': 'objects', 'default_permissions': (), 'verbose_name': 'Image item', 'verbose_name_plural': 'Image items'},
        ),
        migrations.AlterModelOptions(
            name='svgitem',
            options={'base_manager_name': 'objects', 'default_permissions': (), 'verbose_name': 'SVG item', 'verbose_name_plural': 'SVG items'},
        ),
    ]
