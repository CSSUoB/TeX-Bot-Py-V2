"""Custom cog subclass that stores a reference to the custom bot class."""

from collections.abc import Sequence

__all__: Sequence[str] = ("TeXBotBaseCog",)


import contextlib
import logging
import re
from collections.abc import Mapping
from logging import Logger
from typing import TYPE_CHECKING, Final

import discord
from discord import Cog

from exceptions import (
    BaseDoesNotExistError,
    CommitteeRoleDoesNotExistError,
    DiscordMemberNotInMainGuildError,
)
from .tex_bot import TeXBot
from .tex_bot_contexts import TeXBotApplicationContext, TeXBotAutocompleteContext

if TYPE_CHECKING:
    from typing import TypeAlias


if TYPE_CHECKING:
    MentionableMember: TypeAlias = discord.Member | discord.Role

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class TeXBotBaseCog(Cog):
    """Base Cog subclass that stores a reference to the currently running bot."""

    ERROR_ACTIVITIES: Final[Mapping[str, str]] = {
        "archive": "archive the selected category",
        "delete_all_reminders": (
            "delete all `DiscordReminder` objects from the backend database"
        ),
        "delete_all_group_made_members": (
            "delete all `GroupMadeMember` objects from the backend database"
        ),
        "edit_message": "edit the message",
        "induct": "induct user",
        "silent_induct": "silently induct user",
        "non_silent_induct": "induct user and send welcome message",
        "ensure_members_inducted": "ensure all members are inducted",
        "make_member": "make you a member",
        "opt_out_introduction_reminders": "opt-in/out of introduction reminders",
        "ping": "reply to ping",
        "remind_me": "remind you",
        "channel_stats": "display channel statistics",
        "server_stats": "display whole server statistics",
        "user_stats": "display your statistics",
        "left_member_stats": (
            "display statistics about the members that have left the server"
        ),
        "write_roles": "send messages",
    }

    def __init__(self, bot: TeXBot) -> None:
        """Initialize a new cog instance, storing a reference to the bot object."""
        self.bot: TeXBot = bot

    async def command_send_error(self, ctx: TeXBotApplicationContext, error_code: str | None = None, message: str | None = None, logging_message: str | BaseException | None = None) -> None:  # noqa: E501
        """
        Construct & format an error message from the given details.

        The constructed error message is then sent as the response to the given
        application command context.
        """
        COMMAND_NAME: Final[str] = (
            ctx.command.callback.__name__
            if (
                hasattr(ctx.command, "callback")
                and not ctx.command.callback.__name__.startswith("_")
            ) else ctx.command.qualified_name
        )

        await self.send_error(
            self.bot,
            ctx.interaction,
            interaction_name=COMMAND_NAME,
            error_code=error_code,
            message=message,
            logging_message=logging_message,
        )

    @classmethod
    async def send_error(cls, bot: TeXBot, interaction: discord.Interaction, interaction_name: str, error_code: str | None = None, message: str | None = None, logging_message: str | BaseException | None = None) -> None:  # noqa: E501
        """
        Construct & format an error message from the given details.

        The constructed error message is then sent as the response to the given interaction.
        """
        construct_error_message: str = ":warning:There was an error"

        if error_code:
            # noinspection PyUnusedLocal
            committee_mention: str = "committee"

            with contextlib.suppress(CommitteeRoleDoesNotExistError):
                committee_mention = (await bot.committee_role).mention

            construct_error_message = (
                f"**Contact a {committee_mention} member, referencing error code: "
                f"{error_code}**\n"
                + construct_error_message
            )

        if interaction_name in cls.ERROR_ACTIVITIES:
            construct_error_message += (
                f" when trying to {cls.ERROR_ACTIVITIES[interaction_name]}"
            )

        if message:
            construct_error_message += ":"
        else:
            construct_error_message += "."

        construct_error_message += ":warning:"

        if message:
            message = re.sub(
                r"<([@&#]?|(@[&#])?)\d+>",
                lambda match: f"`{match.group(0)}`",
                message.strip(),
            )
            construct_error_message += f"\n`{message}`"

        await interaction.respond(construct_error_message, ephemeral=True)

        if logging_message:
            logger.error(
                " ".join(
                    message_part
                    for message_part
                    in (
                        error_code if error_code else "",
                        f"({interaction_name})",
                        str(logging_message),
                    )
                    if message_part
                ).rstrip(": ;"),
            )

    @staticmethod
    async def autocomplete_get_text_channels(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501
        """
        Autocomplete callable that generates the set of available selectable channels.

        The list of available selectable channels is unique to each member, and is used in any
        slash-command options that have a channel input-type.
        """
        if not ctx.interaction.user:
            return set()

        try:
            main_guild: discord.Guild = ctx.bot.main_guild
            # noinspection PyUnusedLocal
            channel_permissions_limiter: MentionableMember = await ctx.bot.guest_role
        except BaseDoesNotExistError:
            return set()

        with contextlib.suppress(DiscordMemberNotInMainGuildError):
            channel_permissions_limiter = await ctx.bot.get_main_guild_member(
                ctx.interaction.user,
            )

        if not ctx.value or re.match(r"\A#.*\Z", ctx.value):
            return {
                discord.OptionChoice(name=f"#{channel.name}", value=str(channel.id))
                for channel
                in main_guild.text_channels
                if channel.permissions_for(channel_permissions_limiter).is_superset(
                    discord.Permissions(send_messages=True, view_channel=True),
                )
            }

        return {
            discord.OptionChoice(name=channel.name, value=str(channel.id))
            for channel
            in main_guild.text_channels
            if channel.permissions_for(channel_permissions_limiter).is_superset(
                discord.Permissions(send_messages=True, view_channel=True),
            )
        }
