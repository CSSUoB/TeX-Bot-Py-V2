# Generated by Django 5.0.4 on 2024-05-18 17:11

import db.core.models.managers
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_rename_hashed_uob_id_groupmademember_hashed_group_member_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscordMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hashed_discord_id', models.CharField(max_length=64, unique=True, validators=[django.core.validators.RegexValidator('\\A[A-Fa-f0-9]{64}\\Z', 'hashed_discord_id must be a valid sha256 hex-digest.')], verbose_name='Hashed Discord Member ID')),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', db.core.models.managers.HashedDiscordMemberManager()),
            ],
        ),
        migrations.AlterModelOptions(
            name='discordmemberstrikes',
            options={'verbose_name': "Discord Member that has been previously given one or more strikes because they broke one or more of your group's Discord guild rules", 'verbose_name_plural': "Discord Members that have been previously given one or more strikes because they broke one or more of your group's Discord guild rules"},
        ),
        migrations.AlterModelOptions(
            name='introductionreminderoptoutmember',
            options={'verbose_name': 'Discord Member that has Opted-Out of Introduction Reminders', 'verbose_name_plural': 'Discord Members that have Opted-Out of Introduction Reminders'},
        ),
        migrations.AlterModelOptions(
            name='sentgetrolesremindermember',
            options={'verbose_name': 'Discord Member that has had a "Get Roles" reminder sent to their DMs', 'verbose_name_plural': 'Discord Members that have had a "Get Roles" reminder sent to their DMs'},
        ),
        migrations.AlterModelOptions(
            name='sentoneoffintroductionremindermember',
            options={'verbose_name': 'Discord Member that has had a one-off Introduction reminder sent to their DMs', 'verbose_name_plural': 'Discord Members that have had a one-off Introduction reminder sent to their DMs'},
        ),
        migrations.AddField(
            model_name='discordmemberstrikes',
            name='discord_member',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, primary_key=False, related_name='strikes', serialize=False, to='core.discordmember', verbose_name='Discord Member'),
        ),
        migrations.AddField(
            model_name='discordreminder',
            name='discord_member',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='core.discordmember', verbose_name='Discord Member'),
        ),
        migrations.AddField(
            model_name='introductionreminderoptoutmember',
            name='discord_member',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, primary_key=False, related_name='opted_out_of_introduction_reminders', serialize=False, to='core.discordmember', verbose_name='Discord Member'),
        ),
        migrations.AddField(
            model_name='sentgetrolesremindermember',
            name='discord_member',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, primary_key=False, related_name='sent_get_roles_reminder', serialize=False, to='core.discordmember', verbose_name='Discord Member'),
        ),
        migrations.AddField(
            model_name='sentoneoffintroductionremindermember',
            name='discord_member',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, primary_key=False, related_name='sent_one_off_introduction_reminder', serialize=False, to='core.discordmember', verbose_name='Discord Member'),
        ),
    ]
