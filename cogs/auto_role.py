"""Module for automatically assigning roles to new members."""

from typing import TYPE_CHECKING

import discord

from config import settings
from utils import TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence


__all__: "Sequence[str]" = ("AutoRoleCog",)


class AutoRoleCog(TeXBotBaseCog):
    """Cog for automatically assigning roles to new members."""

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Assign roles to new members when they join."""
        if not settings["AUTO_ROLE"]:
            return

        if before.bot or after.bot:
            return

        if not before.pending and after.pending:
            roles_to_add: set[str] = settings["AUTO_ROLES_TO_ADD"]

            if not roles_to_add:
                return

            for role_name in roles_to_add:
                role: discord.Role | None = discord.utils.get(
                    self.bot.main_guild.roles, name=role_name
                )

                if role is None:
                    continue

                await after.add_roles(
                    role, reason="Auto role assignment on passing verification."
                )
