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

    async def add_user_or_role_silently(self, user_or_role: discord.Member | discord.Role, thread: discord.Thread) -> None:  # noqa: E501
        """Add a user or role to a thread without pinging them."""
        message: discord.Message = await thread.send(
            content=f"Adding {user_or_role!r} to thread...",
            silent=True,
        )
        await message.edit(content=f"{user_or_role.mention}")
        await message.delete(delay=1)

    async def add_user_or_role_with_ping(self, user_or_role: discord.Member | discord.Role, thread: discord.Thread) -> None:  # noqa: E501
        """Add a user or role to a thread and ping them."""
        if isinstance(user_or_role, discord.Member):
            await thread.add_user(user=user_or_role)
            return

        if isinstance(user_or_role, discord.Role):
            member: discord.Member
            for member in user_or_role.members:
                try:
                    await thread.add_user(member)
                except discord.NotFound:
                    logger.debug(
                        "User: %s has blocked the bot and "
                        "therefore could not be added to thread: %s.",
                        member,
                        thread
                    )
            return

        logger.debug("User or role: %s is not a valid type.", user_or_role)

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """Add users to a thread when it is created."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role

        if thread.parent is None or thread.parent.category is None:
            return

        if "committee" in thread.parent.category.name.lower():
            await self.add_user_or_role_silently(user_or_role=committee_role, thread=thread)
            await self.add_user_or_role_silently(
                user_or_role=committee_elect_role,
                thread=thread,
            )

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
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="silent",
        description="Whether the users being added should be pinged or not.",
        input_type=bool,
        required=False,
        parameter_name="silent",
    )
    async def add_users_to_thread(self, ctx: "TeXBotApplicationContext", user_or_role: str, silent: bool) -> None:  # noqa: E501, FBT001
        """Add users or roles to a thread."""
        main_guild: discord.Guild = ctx.bot.main_guild

        if not isinstance(ctx.channel, discord.Thread):
            await self.command_send_error(
                ctx=ctx,
                message="This command can only be used in a thread.",
            )
            return

        thread: discord.Thread = ctx.channel

        try:
            user_object: discord.Member = await self.bot.get_member_from_str_id(user_or_role)
        except ValueError:
            pass
        else:
            if silent:
                await self.add_user_or_role_silently(user_object, thread)
            else:
                await self.add_user_or_role_with_ping(user_object, thread)

            await ctx.respond(
                content=f"User {user_object.mention} has been added to the thread."
            )
            return

        try:
            role_id: int = int(user_or_role)
        except ValueError:
            logger.debug("Role or User ID: %s is not a valid ID.", user_or_role)
            await ctx.respond(content=f"The role or user: {user_or_role} is not valid.")
            return

        role_object: discord.Role | None = discord.utils.get(main_guild.roles, id=role_id)
        if role_object is None:
            await self.command_send_error(
                ctx=ctx,
                message=f"The role or user: <@{role_id}> is not valid or couldn't be found.",
            )
            return

        if silent:
            await self.add_user_or_role_silently(role_object, thread)
        else:
            await self.add_user_or_role_with_ping(role_object, thread)

        await ctx.respond(
            content=f"Role {role_object.mention} has been added to the thread."
        )
