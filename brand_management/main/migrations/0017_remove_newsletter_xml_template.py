# Generated by Django 5.1.6 on 2025-02-13 06:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_generatedpdf'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsletter',
            name='xml_template',
        ),
    ]
