# Generated by Django 5.1.6 on 2025-02-19 03:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0037_remove_newsletter_campaign_mappings'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsletter',
            name='is_frozen',
        ),
        migrations.RemoveField(
            model_name='newsletter',
            name='name',
        ),
        migrations.RemoveField(
            model_name='newsletter',
            name='placeholders',
        ),
        migrations.RemoveField(
            model_name='newsletter',
            name='template_content',
        ),
        migrations.AddField(
            model_name='newsletter',
            name='campaigns',
            field=models.ManyToManyField(related_name='newsletters', to='main.campaign'),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='html_template',
            field=models.TextField(null=True),
        ),
    ]
