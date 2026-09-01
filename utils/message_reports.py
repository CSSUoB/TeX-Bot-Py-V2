"""Utility functions for sending copies of Discord messages to committee for review."""

from enum import Enum
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final

    from .tex_bot import TeXBot


__all__: "Sequence[str]" = ("MessageReportAction", "send_message_report_to_committee")


MAXIMUM_REPORTED_CONTENT_LENGTH: "Final[int]" = 600


class MessageReportAction(Enum):
    """Enum class to define the reason a message was sent to committee for review."""

    DELETED = "deleted"
    REPORTED = "reported"


def _format_report_description(message: discord.Message, action: MessageReportAction) -> str:
    """Construct the embed description that holds the reported message's content."""
    description: str

    if message.content:
        description = message.content[:MAXIMUM_REPORTED_CONTENT_LENGTH]
        if len(message.content) > MAXIMUM_REPORTED_CONTENT_LENGTH:
            description += (
                f" _... (truncated to {MAXIMUM_REPORTED_CONTENT_LENGTH} characters)_"
            )
    else:
        description = f"_{action.value.capitalize()} message had no content_"
        if message.attachments or message.embeds:
            description += " _but did have one or more attachments!_"

    description += f"\n[View Original]({message.jump_url})"

    if message.reference:
        description += f"\n[View Message this replied to]({message.reference.jump_url})"

    return description


def _get_report_image_url(message: discord.Message) -> str | None:
    """Retrieve the URL of the given message's only attachment, if it is an image."""
    if len(message.attachments) != 1:
        return None

    attachment_type: str | None = message.attachments[0].content_type

    if not attachment_type or "image" not in attachment_type:
        return None

    return message.attachments[0].url


async def send_message_report_to_committee(
    bot: "TeXBot",
    message: discord.Message,
    reporting_user: discord.User | discord.Member,
    action: MessageReportAction,
) -> None:
    """
    Send a copy of the given message to the message-reports channel, for committee to review.

    Raises `MessageReportsChannelDoesNotExist` if that channel does not exist.
    """
    message_reports_channel: discord.TextChannel = await bot.message_reports_channel

    await message_reports_channel.send(
        content=(
            f"{reporting_user.mention} {action.value} "
            f"a message from {message.author.mention} "
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
            author=discord.EmbedAuthor(
                name=message.author.display_name, icon_url=message.author.display_avatar.url
            ),
            description=_format_report_description(message, action),
            colour=message.author.colour,
            image=_get_report_image_url(message),
            timestamp=message.created_at,
        ),
    )
