# Generated by Django 4.2.5 on 2023-10-07 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_models_fields', '0004_auto_20230506_0349'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuploadedfile',
            name='mimetype',
            field=models.CharField(default='', editable=False, max_length=128, verbose_name='MIME Type'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='customuploadedimage',
            name='mimetype',
            field=models.CharField(default='', editable=False, max_length=128, verbose_name='MIME Type'),
            preserve_default=False,
        ),
    ]
