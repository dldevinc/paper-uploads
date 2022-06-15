# Generated by Django 4.0.2 on 2022-03-25 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0007_uploadedsvgfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='svgitem',
            name='height',
            field=models.DecimalField(decimal_places=4, default=0, editable=False, max_digits=10, verbose_name='height'),
        ),
        migrations.AddField(
            model_name='svgitem',
            name='width',
            field=models.DecimalField(decimal_places=4, default=0, editable=False, max_digits=10, verbose_name='width'),
        ),
        migrations.AddField(
            model_name='uploadedsvgfile',
            name='height',
            field=models.DecimalField(decimal_places=4, default=0, editable=False, max_digits=10, verbose_name='height'),
        ),
        migrations.AddField(
            model_name='uploadedsvgfile',
            name='width',
            field=models.DecimalField(decimal_places=4, default=0, editable=False, max_digits=10, verbose_name='width'),
        ),
    ]