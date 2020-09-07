# Generated by Django 3.0.9 on 2020-09-07 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_auto_20200903_1850'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dummyfilefieldresource',
            old_name='name',
            new_name='basename',
        ),
        migrations.RenameField(
            model_name='dummyfileresource',
            old_name='name',
            new_name='basename',
        ),
        migrations.RenameField(
            model_name='dummyimagefieldresource',
            old_name='name',
            new_name='basename',
        ),
        migrations.RenameField(
            model_name='dummyresource',
            old_name='name',
            new_name='basename',
        ),
        migrations.RenameField(
            model_name='dummyversatileimageresource',
            old_name='name',
            new_name='basename',
        ),
        migrations.AlterField(
            model_name='dummyimagefieldresource',
            name='description',
            field=models.TextField(blank=True, help_text='This text will be used by screen readers, search engines, or when the image cannot be loaded', verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='dummyversatileimageresource',
            name='description',
            field=models.TextField(blank=True, help_text='This text will be used by screen readers, search engines, or when the image cannot be loaded', verbose_name='description'),
        ),
    ]
