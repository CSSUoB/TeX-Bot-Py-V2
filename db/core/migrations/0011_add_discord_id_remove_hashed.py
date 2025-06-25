# Manual migration to replace hashed_discord_id with discord_id

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_assignedcommitteeaction'),  # Adjust based on your latest migration
    ]

    operations = [
        # Step 1: Add the new discord_id column (temporarily nullable)
        migrations.AddField(
            model_name='discordmember',
            name='discord_id',
            field=models.CharField(
                max_length=20,
                null=True,
                blank=True,
                validators=[
                    django.core.validators.RegexValidator(
                        '\\A\\d{17,20}\\Z',
                        'discord_id must be a valid Discord member ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)'
                    )
                ],
                verbose_name='Discord Member ID',
            ),
        ),

        # Step 2: Since hashed Discord IDs cannot be reversed, we need to either:
        # - Clear existing data and start fresh, OR
        # - Manually populate discord_id values from logs/external sources

        # For now, let's clear the existing data to start fresh
        migrations.RunSQL(
            "DELETE FROM core_discordmember;",
            reverse_sql="-- Cannot reverse data deletion"
        ),

        # Step 3: Make discord_id non-nullable and unique
        migrations.AlterField(
            model_name='discordmember',
            name='discord_id',
            field=models.CharField(
                max_length=20,
                unique=True,
                null=False,
                blank=False,
                validators=[
                    django.core.validators.RegexValidator(
                        '\\A\\d{17,20}\\Z',
                        'discord_id must be a valid Discord member ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)'
                    )
                ],
                verbose_name='Discord Member ID',
            ),
        ),

        # Step 4: Remove the old hashed_discord_id column
        migrations.RemoveField(
            model_name='discordmember',
            name='hashed_discord_id',
        ),
    ]
