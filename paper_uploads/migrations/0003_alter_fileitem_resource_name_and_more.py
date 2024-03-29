# Generated by Django 4.0.1 on 2022-02-16 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0002_rename_basename_fileitem_resource_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fileitem',
            name='resource_name',
            field=models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='resource name'),
        ),
        migrations.AlterField(
            model_name='imageitem',
            name='resource_name',
            field=models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='resource name'),
        ),
        migrations.AlterField(
            model_name='svgitem',
            name='resource_name',
            field=models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='resource name'),
        ),
        migrations.AlterField(
            model_name='uploadedfile',
            name='resource_name',
            field=models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='resource name'),
        ),
        migrations.AlterField(
            model_name='uploadedimage',
            name='resource_name',
            field=models.CharField(editable=False, help_text='Human-readable resource name', max_length=255, verbose_name='resource name'),
        ),
    ]
