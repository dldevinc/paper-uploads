# Generated by Django 3.0.8 on 2020-07-24 09:44

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20200723_1446'),
    ]

    operations = [
        migrations.CreateModel(
            name='DummyImageFieldResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('content_hash', models.CharField(editable=False, help_text='hash of the contents of a file', max_length=64, verbose_name='content hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('title', models.CharField(blank=True, help_text='The title is being used as a tooltip when the user hovers the mouse over the image', max_length=255, verbose_name='title')),
                ('description', models.CharField(blank=True, help_text='This text will be used by screen readers, search engines, or when the image cannot be loaded', max_length=255, verbose_name='description')),
                ('width', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='width')),
                ('height', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='height')),
                ('cropregion', models.CharField(blank=True, editable=False, max_length=24, verbose_name='crop region')),
                ('file', models.FileField(upload_to='', verbose_name='file')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
