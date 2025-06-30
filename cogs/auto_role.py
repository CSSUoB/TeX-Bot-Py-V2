"""Module for automatically assigning roles to new members."""

import logging
from typing import TYPE_CHECKING

import discord

from config import settings
from utils import TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


__all__: "Sequence[str]" = ("AutoRoleBaseCog", "AutoRoleListenerCog")


class AutoRoleBaseCog(TeXBotBaseCog):
    """Base class for auto role cogs."""

    async def _auto_add_roles(self, member: discord.Member) -> None:
        """Add roles to a member when they join."""
        logger.debug("auto_add_roles called for %s", member)

        roles_to_add: set[str] = settings["AUTO_ROLES_TO_ADD"]

        if not roles_to_add:
            return

        for role_name in roles_to_add:
            role: discord.Role | None = discord.utils.get(
                self.bot.main_guild.roles, name=role_name
            )

            logger.debug("Found role '%s': %s", role_name, role)

            if role is None:
                continue

            await member.add_roles(role, reason="Auto role assignment on joining.")



class AutoRoleListenerCog(AutoRoleBaseCog):
    """Cog for automatically assigning roles to new members."""

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Assign roles to new members when they join."""
        if not settings["AUTO_ROLE"]:
            return

        logger.debug("on_member_update called for %s", after)

        if before.bot or after.bot:
            return

        if before.pending and not after.pending:
            logger.debug("Member %s has completed pending status.", after)

            await self._auto_add_roles(after)

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_join(self, member: discord.Member) -> None:
        """Assign roles to new members when they join."""
        if not settings["AUTO_ROLE"]:
            return

        logger.debug("on_member_join called for %s", member)

        for slot in member.__slots__:
            logger.debug(f"{slot}: {getattr(member, slot)}")

        logger.debug(str(member))
        logger.debug(member.__slots__)
        logger.debug(member.flags)

        if member.bot:
            return

        if member.pending:
            logger.debug("Member %s is pending, waiting for update.", member)
            return

        await self._auto_add_roles(member)


# TODO: REMOVE THIS COMMAND
    @discord.slash_command(  # type: ignore[misc, no-untyped-call]
        name="pending-check"
    )
    async def pending_check(self, ctx):  # type: ignore[misc, no-untyped-def]
        main_guild: discord.Guild = self.bot.main_guild

        members_ids: set[int] = {member.id for member in ctx.guild.members}

        logger.debug(members_ids)

        for member_id in members_ids:
            member: discord.Member | None = await main_guild.fetch_member(member_id)
            if member is None:
                continue

            await ctx.send(
                f"{member.name} - pending: {member.pending}, rejoined: {member.flags.did_rejoin}, bypass-verification: {member.flags.bypasses_verification}, communication-disabled: {member.communication_disabled_until}"
            )
