# Generated by Django 2.2.5 on 2019-10-10 12:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_document_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='page',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Page'),
        ),
    ]