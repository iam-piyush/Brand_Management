# Generated by Django 5.1.6 on 2025-02-18 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0034_rename_discount_value_coupon_flat_discount_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsletter',
            name='campaign',
        ),
        migrations.RemoveField(
            model_name='newsletter',
            name='status',
        ),
        migrations.RemoveField(
            model_name='newsletter',
            name='subscriber_base',
        ),
        migrations.RemoveField(
            model_name='newsletter',
            name='thumbnail',
        ),
        migrations.AddField(
            model_name='newsletter',
            name='campaign_mappings',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='is_frozen',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='placeholders',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='template_content',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='newsletter',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='newsletter',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='newsletter',
            name='newsletter_id',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
