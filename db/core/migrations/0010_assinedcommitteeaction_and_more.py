# Generated by Django 5.0.6 on 2024-07-22 16:37

import db.core.models.managers
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20240519_0020'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssinedCommitteeAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(max_length=1500, verbose_name='Description')),
                ('status', models.CharField(choices=[('X', 'Cancelled'), ('B', 'Blocked'), ('C', 'Complete'), ('IP', 'In Progress'), ('NS', 'Not Started')], default='NS', max_length=2)),
                ('discord_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_committee_actions', to='core.discordmember', verbose_name='Discord Member')),
            ],
            options={
                'verbose_name': 'Assigned Committee Action',
            },
            managers=[
                ('objects', db.core.models.managers.RelatedDiscordMemberManager()),
            ],
        ),
        migrations.AddConstraint(
            model_name='assinedcommitteeaction',
            constraint=models.UniqueConstraint(fields=('discord_member', 'description'), name='unique_user_action'),
        ),
    ]