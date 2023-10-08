"""Contains cog classes for any write_roles interactions."""

import logging

import discord

from cogs._utils import TeXBotApplicationContext, TeXBotCog
from config import settings
from exceptions import CommitteeRoleDoesNotExist, GuildDoesNotExist, RolesChannelDoesNotExist


class WriteRolesCommandCog(TeXBotCog):
    # noinspection SpellCheckingInspection
    """Cog class that defines the "/writeroles" command and its call-back method."""

    # noinspection SpellCheckingInspection
    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="writeroles",
        description="Populates #roles with the correct messages."
    )
    async def write_roles(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "write_roles" command.

        The "write_roles" command populates the "#roles" channel with the correct messages
        defined in the messages.json file.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            return

        committee_role: discord.Role = await self.bot.committee_role
        if not committee_role:
            await self.send_error(
                ctx,
                error_code="E1021",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        roles_channel: discord.TextChannel | None = await self.bot.roles_channel
        if not roles_channel:
            await self.send_error(
                ctx,
                error_code="E1031",
                logging_message=str(RolesChannelDoesNotExist())
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

        roles_message: str
        for roles_message in settings["ROLES_MESSAGES"]:
            await roles_channel.send(roles_message)

        await ctx.respond("All messages sent successfully.", ephemeral=True)
