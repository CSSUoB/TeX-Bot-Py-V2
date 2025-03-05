"""Contains Cog classes for adding users and roles to threads."""

import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING

import discord

from config import settings
from exceptions import GuestRoleDoesNotExistError, GuildDoesNotExistError
from utils import TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext


__all__: "Sequence[str]" = ("AddUsersToThreadsAndChannelsCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class AddUsersToThreadsAndChannelsCog(TeXBotBaseCog):
    """Cog for adding users to threads."""

    @staticmethod
    async def autocomplete_get_members(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """Autocomplete callable that generates the set of available selectable members."""
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
            guest_role: discord.Role = await ctx.bot.guest_role
        except (GuildDoesNotExistError, GuestRoleDoesNotExistError):
            return set()

        members: set[discord.Member] = {
            member
            for member in main_guild.members
            if not member.bot and guest_role not in member.roles
        }

        if not ctx.value or ctx.value.startswith("@"):
            return {
                discord.OptionChoice(name=f"@{member.name}", value=str(member.id))
                for member in members
            }

        return {
            discord.OptionChoice(name=member.name, value=str(member.id)) for member in members
        }

    @staticmethod
    async def autocomplete_get_roles(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """Autocomplete callable that generates the set of available selectable roles."""
        try:
            main_guild: discord.Guild = ctx.bot.main_guild
        except GuildDoesNotExistError:
            return set()

        if not ctx.value or ctx.value.startswith("@"):
            return {
                discord.OptionChoice(name=f"@{role.name}", value=str(role.id))
                for role in main_guild.roles
            }

        return {
            discord.OptionChoice(name=role.name, value=str(role.id))
            for role in main_guild.roles
        }

    async def add_users_or_roles_silently(
        self,
        users_or_roles: discord.Member
        | discord.Role
        | list[discord.Member]
        | list[discord.Role],
        thread: discord.Thread,
    ) -> None:
        """Add a user or role to a thread without pinging them."""
        if isinstance(users_or_roles, Iterable):
            user_or_role: discord.Role | discord.Member
            for user_or_role in users_or_roles:
                await self.add_users_or_roles_silently(
                    users_or_roles=user_or_role, thread=thread
                )
            return

        message: discord.Message = await thread.send(
            content=f"Adding {users_or_roles!r} to thread...",
            silent=True,
        )
        await message.edit(content=f"{users_or_roles.mention}")
        await message.delete(delay=1)

    async def add_users_or_roles_with_ping(
        self,
        users_or_roles: discord.Member
        | discord.Role
        | list[discord.Member]
        | list[discord.Role],
        thread: discord.Thread,
    ) -> None:
        """Add a user or role to a thread and ping them."""
        if isinstance(users_or_roles, Iterable):
            user_or_role: discord.Role | discord.Member
            for user_or_role in users_or_roles:
                await self.add_users_or_roles_with_ping(
                    users_or_roles=user_or_role, thread=thread
                )
            return

        if isinstance(users_or_roles, discord.Member):
            try:
                await thread.add_user(user=users_or_roles)
            except discord.NotFound:
                logger.debug(
                    "User: %s has blocked the bot and "
                    "therefore could not be added to thread: %s.",
                    users_or_roles,
                    thread,
                )
            return

        if isinstance(users_or_roles, discord.Role):
            member: discord.Member
            for member in users_or_roles.members:
                try:
                    await thread.add_user(member)
                except discord.NotFound:
                    logger.debug(
                        "User: %s has blocked the bot and "
                        "therefore could not be added to thread: %s.",
                        member,
                        thread,
                    )
            return

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """Add users to a thread when it is created."""
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        if not settings["ADD_COMMITTEE_TO_THREADS"]:
            return

        committee_role: discord.Role = await self.bot.committee_role
        committee_elect_role: discord.Role = await self.bot.committee_elect_role

        if thread.parent is None or thread.parent.category is None:
            return

        if "committee" in thread.parent.category.name.lower():
            await self.add_users_or_roles_silently(
                users_or_roles=committee_role, thread=thread
            )
            await self.add_users_or_roles_silently(
                users_or_roles=committee_elect_role,
                thread=thread,
            )

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="add_users_to_channel",
        description="Adds selected users to a channel.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="user",
        description="The user to add to the channel.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_members),  # type: ignore[arg-type]
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
    async def add_user_to_channel(  # type: ignore[misc]
        self,
        ctx: "TeXBotApplicationContext",
        user_id_str: str,
        silent: bool,  # noqa: FBT001
    ) -> None:
        """Add users or roles to a channel."""
        if not isinstance(ctx.channel, discord.TextChannel) and not isinstance(
            ctx.channel, discord.Thread
        ):
            await self.command_send_error(
                ctx=ctx,
                message="This command currently only supports text channels or threads.",
            )
            return

        channel: discord.TextChannel | discord.Thread = ctx.channel

        try:
            user_to_add: discord.Member = await self.bot.get_member_from_str_id(user_id_str)
        except ValueError:
            logger.debug("User ID: %s is not a valid ID.", user_id_str)
            await ctx.respond(content=f"The user: {user_id_str} is not valid.")
            return

        if isinstance(channel, discord.TextChannel):
            await channel.set_permissions(
                target=user_to_add,
                read_messages=True,
                send_messages=True,
                reason=f"User {ctx.user} used TeX-Bot slash-command `add_user_to_channel`.",
            )

            if not silent:
                await channel.send(
                    content=f"{user_to_add.mention} has been added to the channel."
                )

        if isinstance(channel, discord.Thread):
            if silent:
                await self.add_users_or_roles_silently(user_to_add, channel)
            else:
                await self.add_users_or_roles_with_ping(user_to_add, channel)

        await ctx.respond(
            content=f"User {user_to_add.mention} has been added to the channel.",
            ephemeral=True,
        )

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="add_role_to_channel",
        description="Adds the selected role and it's users to a channel.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="role",
        description="The role to add to the channel.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_roles),  # type: ignore[arg-type]
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
    async def add_role_to_channel(  # type: ignore[misc]
        self,
        ctx: "TeXBotApplicationContext",
        role: str,
        silent: bool,  # noqa: FBT001
    ) -> None:
        """Command to add a role to a channel."""
        if not isinstance(ctx.channel, discord.Thread) and not isinstance(
            ctx.channel, discord.TextChannel
        ):
            await self.command_send_error(
                ctx=ctx, message="This command can only be used in a text channel or thread."
            )
            return

        channel: discord.TextChannel | discord.Thread = ctx.channel

        main_guild: discord.Guild = ctx.bot.main_guild

        try:
            role_id: int = int(role)
        except ValueError:
            logger.debug("Role ID: %s is not a valid ID.", role)
            await ctx.respond(content=f"The role: {role} is not valid.")
            return

        role_object: discord.Role | None = discord.utils.get(main_guild.roles, id=role_id)

        if role_object is None:
            await self.command_send_error(
                ctx=ctx,
                message=f"The role: <@{role_id}> is not valid or couldn't be found.",
            )
            return

        if isinstance(channel, discord.TextChannel):
            await channel.set_permissions(
                target=role_object,
                read_messages=True,
                send_messages=True,
                reason=f"User {ctx.user} used TeX-Bot slash-command `add_role_to_channel`.",
            )

            if not silent:
                await channel.send(
                    content=f"{role_object.mention} has been added to the channel."
                )

        if isinstance(channel, discord.Thread):
            if silent:
                await self.add_users_or_roles_silently(role_object, channel)
            else:
                await self.add_users_or_roles_with_ping(role_object, channel)

        await ctx.respond(
            content=f"Role {role_object.mention} has been added to the channel.",
            ephemeral=True,
        )
