# Generated by Django 5.1.6 on 2025-03-17 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0048_alter_newsletter_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsletter',
            name='subscriber_base',
            field=models.TextField(blank=True, null=True),
        ),
    ]
