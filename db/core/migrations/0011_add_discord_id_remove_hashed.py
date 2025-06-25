# Manual migration to replace hashed_discord_id with discord_id

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_assignedcommitteeaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='discordmember',
            name='discord_id',
            field=models.CharField(
                max_length=20,
                null=False,
                blank=False,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        '\\A\\d{17,20}\\Z',
                        'discord_id must be a valid Discord member ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)'
                    )
                ],
                verbose_name='Discord Member ID',
            ),
        ),

        migrations.RunSQL(
            "DELETE FROM core_discordmember;",
            reverse_sql="-- Cannot reverse data deletion"
        ),

        migrations.RemoveField(
            model_name='discordmember',
            name='hashed_discord_id',
        ),
    ]
