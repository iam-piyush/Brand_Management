# Generated by Django 5.1.6 on 2025-02-11 15:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_subscriber_group'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscriber',
            name='brand',
        ),
    ]
