"""File to hold cog classes related to moderation actions and tracking."""

import logging
from typing import TYPE_CHECKING

import discord

from utils import TeXBotBaseCog
from utils.error_capture_decorators import capture_guild_does_not_exist_error

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = ("ModerationCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class ModerationCog(TeXBotBaseCog):
    """Cog to track moderation actions and report them to the committee."""

    most_recently_deleted_message: discord.Message | None = None

    async def _send_message_to_committee(
        self, message: discord.Message, deleter: discord.Member
    ) -> None:
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
                f"{deleter.mention} deleted a message from {message.author.mention} "
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

    @TeXBotBaseCog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Listen for message deletions."""
        if message.guild is None or message.author.bot or message.guild != self.bot.main_guild:
            return

        self.most_recently_deleted_message = message

    @TeXBotBaseCog.listener()
    @capture_guild_does_not_exist_error
    async def on_audit_log_entry(self, entry: discord.AuditLogEntry) -> None:
        """Listen for audit log entries."""
        committee_role: discord.Role = await self.bot.committee_role

        if (
            entry.action != discord.AuditLogAction.message_delete
            or not self.most_recently_deleted_message
        ):
            return

        deleter: discord.Member | discord.User | None = entry.user
        author: discord.User | discord.Member | None = entry.target
        channel: discord.TextChannel | None = entry.extra.channel  # type: ignore[union-attr]

        if (
            not isinstance(channel, discord.TextChannel)
            or not isinstance(author, discord.Member)
            or not isinstance(deleter, discord.Member)
        ):
            return

        if (
            author != self.most_recently_deleted_message.author
            or channel != self.most_recently_deleted_message.channel
            or committee_role in author.roles
        ):
            return

        self.most_recently_deleted_message = None

        await self._send_message_to_committee(self.most_recently_deleted_message, deleter)
