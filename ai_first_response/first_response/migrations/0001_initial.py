# Generated by Django 5.2.4 on 2025-07-25 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmergencyCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Display name for the emergency category', max_length=100)),
                ('quick_message', models.TextField(help_text='Pre-filled message when user clicks this category')),
                ('icon', models.CharField(help_text='Emoji icon for the category', max_length=10)),
                ('css_class', models.CharField(default='btn-outline-danger', help_text='Bootstrap CSS class for the button', max_length=50)),
                ('is_active', models.BooleanField(default=True, help_text='Whether to show this category')),
                ('order', models.PositiveIntegerField(default=0, help_text='Display order (lower numbers first)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Emergency Category',
                'verbose_name_plural': 'Emergency Categories',
                'ordering': ['order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='ReceivedMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_message', models.TextField(help_text='Original message from user')),
                ('user_latitude', models.FloatField(help_text="User's latitude coordinate")),
                ('user_longitude', models.FloatField(help_text="User's longitude coordinate")),
                ('ai_category', models.CharField(blank=True, help_text='AI classified category', max_length=100)),
                ('ai_severity', models.CharField(blank=True, choices=[('CRIT', 'Critical'), ('HIGH', 'High'), ('MED', 'Medium'), ('LOW', 'Low'), ('INFO', 'Information')], help_text='AI classified severity level', max_length=4)),
                ('ai_instructions', models.JSONField(default=list, help_text='AI generated instructions')),
                ('external_feed', models.TextField(blank=True, help_text='External data feed used for context')),
                ('response_time_ms', models.PositiveIntegerField(blank=True, help_text='Response time in milliseconds', null=True)),
                ('user_ip', models.GenericIPAddressField(blank=True, help_text="User's IP address", null=True)),
                ('user_agent', models.TextField(blank=True, help_text="User's browser user agent")),
                ('session_key', models.CharField(blank=True, help_text="User's session key", max_length=40)),
                ('received_at', models.DateTimeField(auto_now_add=True, help_text='When message was received')),
                ('processed_at', models.DateTimeField(blank=True, help_text='When AI finished processing', null=True)),
                ('is_test_message', models.BooleanField(default=False, help_text='Mark as test/demo message')),
                ('has_error', models.BooleanField(default=False, help_text='Whether processing had errors')),
                ('error_message', models.TextField(blank=True, help_text='Error details if any')),
            ],
            options={
                'verbose_name': 'Received Message',
                'verbose_name_plural': 'Received Messages',
                'ordering': ['-received_at'],
                'indexes': [models.Index(fields=['received_at'], name='first_respo_receive_3c449f_idx'), models.Index(fields=['ai_severity'], name='first_respo_ai_seve_4196a3_idx'), models.Index(fields=['ai_category'], name='first_respo_ai_cate_32e963_idx'), models.Index(fields=['user_latitude', 'user_longitude'], name='first_respo_user_la_287dc9_idx')],
            },
        ),
    ]
