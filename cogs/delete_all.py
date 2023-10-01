import logging

import discord
from django.db.models import Model

from cogs._utils import TeXBotCog
from db.core.models import DiscordReminder, UoBMadeMember
from exceptions import CommitteeRoleDoesNotExist, GuildDoesNotExist


class DeleteAllCommandsCog(TeXBotCog):
    delete_all: discord.SlashCommandGroup = discord.SlashCommandGroup(
        "delete-all",
        "Delete all instances of the selected object type from the backend database"
    )

    async def _delete_all(self, ctx: discord.ApplicationContext, delete_model: type[Model]) -> None:  # noqa: E501
        """Perform the actual deletion process of all instances of the given model class."""
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            return

        committee_role: discord.Role | None = await self.bot.committee_role
        if not committee_role:
            await self.send_error(
                ctx,
                error_code="E1021",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        if committee_role not in interaction_member.roles:
            committee_role_mention: str = "@Committee"
            if ctx.guild:
                committee_role_mention = committee_role.mention

            await self.send_error(
                ctx,
                message=f"Only {committee_role_mention} members can run this command."
            )
            return

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
    async def delete_all_reminders(self, ctx: discord.ApplicationContext) -> None:
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
    async def delete_all_uob_made_members(self, ctx: discord.ApplicationContext) -> None:
        """
        Definition & callback response of the "delete_all_uob_made_members" command.

        The "delete_all_uob_made_members" uses the _delete_all() function to delete all
         UoBMadeMember instance objects stored in the database.
        """
        await self._delete_all(ctx, delete_model=UoBMadeMember)
