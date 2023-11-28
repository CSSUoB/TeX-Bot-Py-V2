"""Contains cog classes for any delete_all interactions."""

import discord
from discord.ext import commands
from django.db.models import Model

from db.core.models import DiscordReminder, UoBMadeMember
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog


class DeleteAllCommandsCog(TeXBotBaseCog):
    """Cog class that defines the "/delete-all" command group and command call-back methods."""

    delete_all: discord.SlashCommandGroup = discord.SlashCommandGroup(
        "delete-all",
        "Delete all instances of the selected object type from the backend database"
    )

    @staticmethod
    async def _delete_all(ctx: TeXBotApplicationContext, delete_model: type[Model]) -> None:
        """Perform the actual deletion process of all instances of the given model class."""
        # noinspection PyProtectedMember
        await delete_model._default_manager.all().adelete()  # noqa: SLF001

        await ctx.respond(
            f"""All {
                "Reminders"
                if delete_model == DiscordReminder
                else
                    "UoB Made Members"
                    if delete_model == UoBMadeMember
                    else "objects"
            } deleted successfully.""",
            ephemeral=True
        )

    @delete_all.command(
        name="reminders",
        description="Deletes all Reminders from the backend database."
    )
    @commands.check_any(commands.check(Checks.check_interaction_user_in_css_guild))  # type: ignore[arg-type]
    @commands.check_any(commands.check(Checks.check_interaction_user_has_committee_role))  # type: ignore[arg-type]
    async def delete_all_reminders(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "delete_all_uob_made_members" command.

        The "delete_all_uob_made_members" uses the _delete_all() function to delete all
        UoBMadeMember instance objects stored in the database.
        """
        await self._delete_all(ctx, delete_model=DiscordReminder)

    @delete_all.command(
        name="uob-made-members",
        description="Deletes all UoB Made Members from the backend database."
    )
    @commands.check_any(commands.check(Checks.check_interaction_user_in_css_guild))  # type: ignore[arg-type]
    @commands.check_any(commands.check(Checks.check_interaction_user_has_committee_role))  # type: ignore[arg-type]
    async def delete_all_uob_made_members(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "delete_all_uob_made_members" command.

        The "delete_all_uob_made_members" uses the _delete_all() function to delete all
         UoBMadeMember instance objects stored in the database.
        """
        await self._delete_all(ctx, delete_model=UoBMadeMember)
