# Generated by Django 3.2.9 on 2021-11-16 07:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0005_alter_collectionitembase_index_together'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fileitem',
            name='owner_app_label',
        ),
        migrations.RemoveField(
            model_name='fileitem',
            name='owner_fieldname',
        ),
        migrations.RemoveField(
            model_name='fileitem',
            name='owner_model_name',
        ),
        migrations.RemoveField(
            model_name='imageitem',
            name='owner_app_label',
        ),
        migrations.RemoveField(
            model_name='imageitem',
            name='owner_fieldname',
        ),
        migrations.RemoveField(
            model_name='imageitem',
            name='owner_model_name',
        ),
        migrations.RemoveField(
            model_name='svgitem',
            name='owner_app_label',
        ),
        migrations.RemoveField(
            model_name='svgitem',
            name='owner_fieldname',
        ),
        migrations.RemoveField(
            model_name='svgitem',
            name='owner_model_name',
        ),
    ]
