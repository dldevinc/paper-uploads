# Generated by Django 4.0.1 on 2022-02-16 10:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dummyfilefieldresource',
            old_name='basename',
            new_name='resource_name',
        ),
        migrations.RenameField(
            model_name='dummyfileresource',
            old_name='basename',
            new_name='resource_name',
        ),
        migrations.RenameField(
            model_name='dummyimagefieldresource',
            old_name='basename',
            new_name='resource_name',
        ),
        migrations.RenameField(
            model_name='dummyversatileimageresource',
            old_name='basename',
            new_name='resource_name',
        ),
    ]
