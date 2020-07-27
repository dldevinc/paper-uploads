# Generated by Django 3.0.8 on 2020-07-23 14:46

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_dummyfileresource'),
    ]

    operations = [
        migrations.CreateModel(
            name='DummyFileFieldResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='changed at')),
                ('content_hash', models.CharField(editable=False, help_text='hash of the contents of a file', max_length=64, verbose_name='content hash')),
                ('extension', models.CharField(editable=False, help_text='Lowercase, without leading dot', max_length=32, verbose_name='extension')),
                ('size', models.PositiveIntegerField(default=0, editable=False, verbose_name='size')),
                ('file', models.FileField(upload_to='', verbose_name='file')),
            ],
            options={
                'abstract': False,
                'default_permissions': (),
            },
        ),
        migrations.AlterField(
            model_name='dummyfileresource',
            name='name',
            field=models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='dummyhashableresource',
            name='name',
            field=models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='dummyresource',
            name='name',
            field=models.CharField(editable=False, help_text='human readable resource name', max_length=255, verbose_name='name'),
        ),
    ]
