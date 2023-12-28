"""Contains cog classes for any delete_all interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("DeleteAllCommandsCog",)

import discord

from db.core.models import DiscordReminder, GroupMadeMember
from db.core.models.utils import AsyncBaseModel
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog


class DeleteAllCommandsCog(TeXBotBaseCog):
    """Cog class that defines the "/delete-all" command group and command call-back methods."""

    delete_all: discord.SlashCommandGroup = discord.SlashCommandGroup(
        "delete-all",
        "Delete all instances of the selected object type from the backend database"
    )

    @staticmethod
    async def _delete_all(ctx: TeXBotApplicationContext, delete_model: type[AsyncBaseModel]) -> None:  # noqa: E501
        """Perform the actual deletion process of all instances of the given model class."""
        # noinspection PyProtectedMember
        await delete_model._default_manager.all().adelete()

        delete_model_instances_name_plural: str = (
            delete_model.INSTANCES_NAME_PLURAL
            if hasattr(delete_model, "INSTANCES_NAME_PLURAL")
            else "objects"
        )

        await ctx.respond(
            f"All {delete_model_instances_name_plural} deleted successfully.",
            ephemeral=True
        )

    @delete_all.command(
        name="reminders",
        description="Deletes all Reminders from the backend database."
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def delete_all_reminders(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "delete_all_group_made_members" command.

        The "delete_all_group_made_members" uses the _delete_all() function to delete all
        UoBMadeMember instance objects stored in the database.
        """
        await self._delete_all(ctx, delete_model=DiscordReminder)

    @delete_all.command(
        name="group-made-members",
        description="Deletes all UoB Made Members from the backend database."
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def delete_all_group_made_members(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "delete_all_group_made_members" command.

        The "delete_all_group_made_members" uses the _delete_all() function to delete all
         UoBMadeMember instance objects stored in the database.
        """
        await self._delete_all(ctx, delete_model=GroupMadeMember)
