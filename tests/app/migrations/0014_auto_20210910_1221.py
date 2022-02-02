# Generated by Django 3.2.6 on 2021-09-10 12:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('paper_uploads', '0003_auto_20210906_1505'),
        ('app', '0013_auto_20210910_1112'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CustomImageItem',
        ),
        migrations.CreateModel(
            name='CustomImageItem',
            fields=[
            ],
            options={
                'proxy': True,
                'default_permissions': (),
                'indexes': [],
                'constraints': [],
            },
            bases=('paper_uploads.imageitem',),
        ),
    ]