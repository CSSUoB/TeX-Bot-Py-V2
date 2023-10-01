import logging

import discord

from cogs._utils import TeXBotCog
from exceptions import (
    CommitteeRoleDoesNotExist,
    GuestRoleDoesNotExist,
    GuildDoesNotExist,
    MemberRoleDoesNotExist,
)


class EnsureMembersInductedCommandCog(TeXBotCog):
    # noinspection SpellCheckingInspection
    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="ensure-members-inducted",
        description="Ensures all users with the @Member role also have the @Guest role."
    )
    async def ensure_members_inducted(self, ctx: discord.ApplicationContext) -> None:
        """
        Definition & callback response of the "ensure_members_inducted" command.

        The "ensure_members_inducted" command ensures that users within the CSS Discord server
        that have the "Member" role have also been given the "Guest" role.
        """
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
                logging_message=CommitteeRoleDoesNotExist()
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

        member_role: discord.Role | None = await self.bot.member_role
        if not member_role:
            await self.send_error(
                ctx,
                error_code="E1023",
                logging_message=MemberRoleDoesNotExist()
            )
            return

        guest_role: discord.Role | None = await self.bot.guest_role
        if not guest_role:
            await self.send_error(
                ctx,
                error_code="E1022",
                logging_message=GuestRoleDoesNotExist()
            )
            return

        await ctx.defer(ephemeral=True)

        changes_made: bool = False

        member: discord.Member
        for member in guild.members:
            if guest_role in member.roles:
                continue

            if member_role in member.roles and guest_role not in member.roles:
                changes_made = True
                await member.add_roles(
                    guest_role,
                    reason=(
                        f"{ctx.user} used TeX Bot slash-command: \"/ensure-members-inducted\""
                    )
                )

        if changes_made:
            await ctx.respond("All members successfully inducted", ephemeral=True)
        else:
            await ctx.respond("No members required inducting", ephemeral=True)
