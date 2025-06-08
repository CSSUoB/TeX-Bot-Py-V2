"""Module for spam protection commands."""

from typing import TYPE_CHECKING

from utils import TeXBotBaseCog

import discord

if TYPE_CHECKING:
    from collections.abc import Sequence


__all__: "Sequence[str]" = ("SpamProtectionListenerCog", )


class SpamProtectionListenerCog(TeXBotBaseCog):
    """Cog for spam checking events."""

    @TeXBotBaseCog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Event to catch messages and check for spam."""
        if message.author.bot:
            return

        last_messages: list[discord.Message] = await message.channel.history(limit=3, before=message).flatten()



