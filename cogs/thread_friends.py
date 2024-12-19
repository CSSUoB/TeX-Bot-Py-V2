"""Contains Cog classes for adding users and roles to threads."""

import logging
from typing import TYPE_CHECKING

import discord

from exceptions import GuestRoleDoesNotExistError, GuildDoesNotExistError
from utils import TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext


__all__: "Sequence[str]" = ("AddUsersToThreadsCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class AddUsersToThreadsCog(TeXBotBaseCog):
    """Cog for adding users to threads."""

    @staticmethod
    async def autocomplete_get_members_and_roles(ctx: "TeXBotAutocompleteContext") -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":  # noqa: E501
        """
        Autocomplete callable that generates the set of available selectable members.

        This list of selectable members is used in any of the "induct" slash-command options
        that have a member input-type.
        """
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
            guest_role: discord.Role = await ctx.bot.guest_role
        except (GuildDoesNotExistError, GuestRoleDoesNotExistError):
            return set()

        members: set[discord.Member | discord.Role] = {
            member
            for member in main_guild.members
            if not member.bot and guest_role in member.roles
        }

        members.update(main_guild.roles)

        if not ctx.value or ctx.value.startswith("@"):
            return {
                discord.OptionChoice(name=f"@{member.name}", value=str(member.id))
                for member in members
            }

        return {
            discord.OptionChoice(name=member.name, value=str(member.id)) for member in members
        }


    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """Add users to a thread when it is created."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role
        parent_channel: discord.TextChannel | discord.ForumChannel | None = thread.parent
        if parent_channel is None:
            return

        parent_channel_category: discord.CategoryChannel | None = parent_channel.category
        if not isinstance(parent_channel_category, discord.CategoryChannel):
            return

        if "committee" in thread.parent.category.name.lower():
            initial_message = await thread.send(content="Adding committee members to thread...", silent=True)
            await initial_message.edit(content=f"{committee_elect_role.mention} {committee_role.mention}")
            await initial_message.delete(delay=1)
            return

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="add_users_to_thread",
        description="Adds selected users to a thread.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user_or_role",
        description="The user or role to add to the thread.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_members_and_roles),  # type: ignore[arg-type]
        required=True,
        parameter_name="user_or_role",
    )
    async def add_users_to_thread(self, ctx: "TeXBotApplicationContext", user_or_role: str) -> None:  # noqa: E501
        """Method for adding users to a thread."""
        main_guild: discord.Guild = ctx.bot.main_guild

        if not isinstance(ctx.channel, discord.Thread):
            await self.command_send_error(
                ctx=ctx,
                message="This command can only be used in a thread.",
            )
            return

        try:
            user_object: discord.Member = await self.bot.get_member_from_str_id(user_or_role)
        except ValueError:
            logger.debug("User ID: %s is not a valid user ID.", user_or_role)
        else:
            await ctx.channel.add_user(user=user_object)
            await ctx.respond(content=f"User: {user_object} added to thread: {ctx.channel}")
            return

        role_object: discord.Role | None = discord.utils.get(main_guild.roles, id=user_or_role)
        await ctx.respond(f"Role: {role_object}, ID: {user_or_role}")
        if role_object is None:
            await self.command_send_error(
                ctx=ctx,
                message="The role you entered does not exist or the user could not be found.",
            )
            return

