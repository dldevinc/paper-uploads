# Generated by Django 3.2.19 on 2023-05-06 03:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('validators_fields', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
