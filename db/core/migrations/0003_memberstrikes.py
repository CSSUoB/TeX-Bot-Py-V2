# Generated by Django 4.2.5 on 2023-09-16 00:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_rename_channel_type_discordreminder__channel_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberStrikes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hashed_member_id', models.CharField(max_length=64, unique=True, validators=[django.core.validators.RegexValidator('\\A[A-Fa-f0-9]{64}\\Z', 'hashed_member_id must be a valid sha256 hex-digest.')], verbose_name='Hashed Discord Member ID')),
                ('strikes', models.PositiveIntegerField(blank=True, default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Number of strikes')),
            ],
            options={
                'verbose_name': 'Hashed Discord ID of Member that has been previously given one or more strikes because they broke one or more of the CSS Discord server rules',
                'verbose_name_plural': 'Hashed Discord IDs of Members that have been previously given one or more strikes because they broke one or more of the CSS Discord server rules',
            },
        ),
    ]
