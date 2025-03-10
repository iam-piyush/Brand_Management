# Generated by Django 5.1.6 on 2025-02-13 04:13

import django.db.models.deletion
import main.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_alter_newsletter_campaign'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneratedPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('newsletter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pdfs', to='main.newsletter')),
                ('subscriber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.subscriber')),
            ],
        ),
    ]
