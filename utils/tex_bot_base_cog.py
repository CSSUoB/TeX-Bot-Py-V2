"""Custom cog subclass that stores a reference to the custom bot class."""

import contextlib
import logging
import re
from typing import TYPE_CHECKING, override

import discord
from discord import Cog

from exceptions import DiscordMemberNotInMainGuildError
from exceptions.base import BaseDoesNotExistError

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from .tex_bot import TeXBot
    from .tex_bot_contexts import TeXBotApplicationContext, TeXBotAutocompleteContext


__all__: "Sequence[str]" = ("TeXBotBaseCog",)


if TYPE_CHECKING:
    type MentionableMember = discord.Member | discord.Role

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class TeXBotBaseCog(Cog):
    """Base Cog subclass that stores a reference to the currently running TeXBot instance."""

    ERROR_ACTIVITIES: "Final[Mapping[str, str]]" = {  # noqa: RUF012
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

    @override
    def __init__(self, bot: "TeXBot") -> None:
        """
        Initialise a new cog instance.

        During initialisation, a reference to the currently running TeXBot instance is stored.
        """
        self.bot: TeXBot = bot  # NOTE: See https://github.com/CSSUoB/TeX-Bot-Py-V2/issues/261

    async def command_send_error(
        self,
        ctx: "TeXBotApplicationContext",
        error_code: str | None = None,
        message: str | None = None,
        logging_message: str | BaseException | None = None,
    ) -> None:
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
            )
            else ctx.command.qualified_name
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
    async def send_error(
        cls,
        bot: "TeXBot",
        interaction: discord.Interaction,
        interaction_name: str,
        error_code: str | None = None,
        message: str | None = None,
        logging_message: str | BaseException | None = None,
    ) -> None:
        """
        Construct & format an error message from the given details.

        The constructed error message is then sent as the response to the given interaction.
        """
        construct_error_message: str = ":warning:There was an error"

        if error_code:
            construct_error_message = (
                f"**Contact a {
                    await bot.get_mention_string(bot.committee_role, default='committee')
                } member, referencing error code: "
                f"{error_code}**\n"
            ) + construct_error_message

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
                r"<([@&#]?|(@[&#])?)\d+>", lambda match: f"`{match.group(0)}`", message.strip()
            )
            construct_error_message += f"\n`{message}`"

        await interaction.respond(construct_error_message, ephemeral=True)

        if logging_message:
            logger.error(
                " ".join(
                    message_part
                    for message_part in (
                        error_code or "",
                        f"({interaction_name})",
                        str(logging_message),
                    )
                    if message_part
                ).rstrip(": ;")
            )

    @staticmethod
    async def autocomplete_get_text_channels(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """
        Autocomplete callable that generates the set of available selectable channels.

        The list of available selectable channels is unique to each member and is used in any
        slash-command options that have a channel input-type.
        """
        if not ctx.interaction.user:
            return set()

        try:
            main_guild: discord.Guild = ctx.bot.main_guild
            channel_permissions_limiter: MentionableMember = await ctx.bot.guest_role
        except BaseDoesNotExistError:
            return set()

        with contextlib.suppress(DiscordMemberNotInMainGuildError):
            channel_permissions_limiter = await ctx.bot.get_main_guild_member(
                ctx.interaction.user
            )

        if not ctx.value or re.fullmatch(r"\A#.*\Z", ctx.value):
            return {
                discord.OptionChoice(name=f"#{channel.name}", value=str(channel.id))
                for channel in main_guild.text_channels
                if channel.permissions_for(channel_permissions_limiter).is_superset(
                    discord.Permissions(send_messages=True, view_channel=True)
                )
            }

        return {
            discord.OptionChoice(name=channel.name, value=str(channel.id))
            for channel in main_guild.text_channels
            if channel.permissions_for(channel_permissions_limiter).is_superset(
                discord.Permissions(send_messages=True, view_channel=True),
            )
        }

    async def send_message_to_committee(
        self, message: discord.Message, interaction_user: discord.Member
    ) -> None:
        """Send a copy of the given message to the committee channel for review."""
        discord_channel: discord.TextChannel | None = discord.utils.get(
            self.bot.main_guild.text_channels,
            name="discord",  # TODO: Make this user-configurable  # noqa: FIX002
        )

        if not discord_channel:
            logger.error("Could not find the channel to send the message deletion report to!")
            return

        embed_content: str = ""

        if message.content:
            embed_content += message.content[:600]
            if len(message.content) > 600:
                embed_content += " _... (truncated to 600 characters)_"
        else:
            embed_content += "_Deleted message had no content_"
            if len(message.attachments) > 0 or len(message.embeds) > 0:
                embed_content += " _but did have one or more attachments!_"

        embed_content += f"\n[View Original]({message.jump_url})"

        if message.reference:
            embed_content += f"\n[View Message this replied to]({message.reference.jump_url})"

        message_author_avatar_url: str | None = message.author.display_avatar.url

        embed_author: discord.EmbedAuthor = discord.EmbedAuthor(
            name=message.author.display_name, icon_url=message_author_avatar_url
        )

        embed_image: str | None = None
        if len(message.attachments) == 1:
            attachment_type: str | None = message.attachments[0].content_type
            if attachment_type and "image" in attachment_type:
                embed_image = message.attachments[0].url

        await discord_channel.send(
            content=(
                f"{interaction_user.mention} deleted a message from {message.author.mention} "
                f"in {
                    message.channel.mention
                    if isinstance(
                        message.channel,
                        (
                            discord.TextChannel,
                            discord.VoiceChannel,
                            discord.StageChannel,
                            discord.Thread,
                        ),
                    )
                    else message.channel
                }:"
            ),
            embed=discord.Embed(
                author=embed_author,
                description=embed_content,
                colour=message.author.colour,
                image=embed_image,
            ),
        )
