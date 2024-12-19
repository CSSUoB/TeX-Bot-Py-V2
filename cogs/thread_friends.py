"""Contains Cog classes for adding users and roles to threads."""

import logging
from typing import TYPE_CHECKING
import discord

from cogs import command_error
from utils import TeXBotBaseCog, TeXBotApplicationContext
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = ()


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class AddUsersToThreadsCog(TeXBotBaseCog):
    """Cog for adding users to threads."""

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """Add users to a thread when it is created."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.bot.main_guild
        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role

        if thread.parent.category and "committee" in thread.parent.category.name:
            committee_member: discord.Member
            for committee_member in committee_role.members:
                await thread.add_user(user=committee_member)

            committee_elect_member: discord.Member
            for committee_elect_member in committee_elect_role.members:
                await thread.add_user(user=committee_elect_member)

    @discord.slash_command(
        name="add_users_to_thread",
        description="Adds selected users to a thread.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user_or_role",
        description="The user or role to add to the thread.",
        input_type=str,
        required=True,
        parameter_name="user_or_role",
    )
    async def add_users_to_thread(self, ctx: TeXBotApplicationContext, user_or_role: discord.User | discord.Member | discord.Role) -> None:
        """Method for adding users to a thread."""

        if not isinstance(ctx.channel, discord.Thread):
            await self.command_send_error(
                ctx=ctx,
                message="This command can only be used in a thread.",
            )
            return
        
        if isinstance(user_or_role, discord.User):
            await self.command_send_error(ctx=ctx, message="User is not in the server.")
            return
        
        await ctx.respond("Input: " + str(user_or_role))

