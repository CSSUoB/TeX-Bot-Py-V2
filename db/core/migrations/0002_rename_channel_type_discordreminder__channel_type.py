# Generated by Django 4.2.3 on 2023-09-08 15:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='discordreminder',
            old_name='channel_type',
            new_name='_channel_type',
        ),
    ]
