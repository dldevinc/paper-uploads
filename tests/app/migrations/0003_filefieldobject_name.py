# Generated by Django 3.0.10 on 2020-09-27 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20200915_0708'),
    ]

    operations = [
        migrations.AddField(
            model_name='filefieldobject',
            name='name',
            field=models.CharField(default='', max_length=128, verbose_name='name'),
            preserve_default=False,
        ),
    ]
