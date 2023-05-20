# Generated by Django 4.2.1 on 2023-05-20 19:53

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Discord_Reminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hashed_member_id', models.CharField(max_length=64, validators=[django.core.validators.RegexValidator('\\A[A-Fa-f0-9]{64}\\Z', 'hashed_member_id must be a valid sha256 hex-digest.')], verbose_name='Hashed Discord Member ID')),
                ('message', models.TextField(blank=True, max_length=1500, verbose_name='Message to remind User')),
                ('_channel_id', models.CharField(max_length=30, validators=[django.core.validators.RegexValidator('\\A\\d{17,20}\\Z', 'channel_id must be a valid Discord channel ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)')], verbose_name='Discord Channel ID Reminder needs to be sent in')),
                ('channel_type', models.IntegerField(blank=True, choices=[(0, 'text'), (1, 'private'), (2, 'voice'), (3, 'group'), (4, 'category'), (5, 'news'), (10, 'news_thread'), (11, 'public_thread'), (12, 'private_thread'), (13, 'stage_voice'), (14, 'directory'), (15, 'forum')], null=True, verbose_name='Discord Channel Type Reminder needs to be sent in')),
                ('send_datetime', models.DateTimeField(verbose_name='Date & time to send Reminder at')),
            ],
            options={
                'verbose_name': 'A Reminder for a Discord User.',
            },
        ),
        migrations.CreateModel(
            name='Interaction_Reminder_Opt_Out_Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hashed_member_id', models.CharField(max_length=64, unique=True, validators=[django.core.validators.RegexValidator('\\A[A-Fa-f0-9]{64}\\Z', 'hashed_member_id must be a valid sha256 hex-digest.')], verbose_name='Hashed Discord Member ID')),
            ],
            options={
                'verbose_name': 'Hashed Discord ID of Member that has Opted-Out of Interaction Reminders',
            },
        ),
        migrations.CreateModel(
            name='Left_Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_roles', models.JSONField()),
            ],
            options={
                'verbose_name': 'A List of Roles that a Member had when they left the CSS Discord server.',
            },
        ),
        migrations.CreateModel(
            name='Sent_Get_Roles_Reminder_Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hashed_member_id', models.CharField(max_length=64, unique=True, validators=[django.core.validators.RegexValidator('\\A[A-Fa-f0-9]{64}\\Z', 'hashed_member_id must be a valid sha256 hex-digest.')], verbose_name='Hashed Discord Member ID')),
            ],
            options={
                'verbose_name': 'Hashed Discord ID of Member that has had a "Get Roles" Reminder sent to their DMs',
            },
        ),
        migrations.CreateModel(
            name='UoB_Made_Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hashed_uob_id', models.CharField(max_length=64, unique=True, validators=[django.core.validators.RegexValidator('\\A[A-Fa-f\\d]{64}\\Z', 'hashed_uob_id must be a valid sha256 hex-digest.')], verbose_name='Hashed UoB ID')),
            ],
            options={
                'verbose_name': 'Hashed UoB ID of User that has been made Member',
            },
        ),
        migrations.AddConstraint(
            model_name='discord_reminder',
            constraint=models.UniqueConstraint(fields=('hashed_member_id', 'message', '_channel_id'), name='unique_user_channel_message'),
        ),
    ]
