# Generated by Django 4.0.1 on 2022-02-16 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_rename_basename_dummyfilefieldresource_resource_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dummyfilefieldresource',
            name='resource_name',
            field=models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='resource name'),
        ),
        migrations.AlterField(
            model_name='dummyfileresource',
            name='resource_name',
            field=models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='resource name'),
        ),
        migrations.AlterField(
            model_name='dummyimagefieldresource',
            name='resource_name',
            field=models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='resource name'),
        ),
        migrations.AlterField(
            model_name='dummyversatileimageresource',
            name='resource_name',
            field=models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='resource name'),
        ),
    ]
