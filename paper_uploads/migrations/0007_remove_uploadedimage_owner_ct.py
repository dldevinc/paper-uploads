# Generated by Django 2.2.5 on 2019-09-11 12:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0006_auto_20190911_1204'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uploadedimage',
            name='owner_ct',
        ),
    ]
