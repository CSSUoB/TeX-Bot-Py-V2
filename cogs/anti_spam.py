"""Module for the anti-spam functionality of the bot."""

from typing import TYPE_CHECKING
from utils import TeXBotBaseCog
import discord

if TYPE_CHECKING
    from collections.abc import Sequence


__all__: "Sequence[str]" = ("AntiSpamCog",)


class AntiSpamCog(TeXBotBaseCog):
    """Cog class that defines the anti-spam functionality."""

    @TeXBotBaseCog.listener()
    async def on_message(self, message: discord.Message) -> None:
        author: discord.Member = message.author

        if author.bot:
            return

        message_history: list[discord.Message] = await author.history(limit=2).flatten()

        if len(message_history) < 2:
            return
        
        


