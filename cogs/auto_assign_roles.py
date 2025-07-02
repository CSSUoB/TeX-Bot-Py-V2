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


__all__: "Sequence[str]" = ("AutoAssignRolesCog",)


class AutoAssignRolesCog(TeXBotBaseCog):
    """Cog for automatically assigning roles to new members."""

    async def _assign_automatic_roles(self, member: discord.Member) -> None:
        """Add roles to a member when they join."""
        roles_to_add: set[str] = settings["AUTO_ROLES_TO_ADD"]

        if not roles_to_add:
            return

        for role_name in roles_to_add:
            role: discord.Role | None = discord.utils.get(
                self.bot.main_guild.roles, name=role_name
            )

            if role is None:
                continue

            await member.add_roles(role, reason="Auto role assignment on joining.")

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Assign roles to new members when they join."""
        if not settings["AUTO_ROLE"] or before.bot or after.bot or after.pending:
            return

        if not after.pending:
            await self._assign_automatic_roles(after)

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_join(self, member: discord.Member) -> None:
        """Assign roles to new members when they join."""
        if not settings["AUTO_ROLE"] or member.bot or member.pending:
            return

        await self._assign_automatic_roles(member)
