"""Class definitions of components that send provided message content to a defined endpoint."""

from collections.abc import Sequence

__all__: Sequence[str] = [
    "MessageSenderComponent",
    "ChannelMessageSender",
    "ResponseMessageSender"
]

from typing import Any, TypedDict

import discord
from discord.ui import View

from utils.tex_bot_contexts import TeXBotApplicationContext


class MessageSenderComponent(Protocol):
    """
    Abstract protocol definition of a sending component.

    Defines the way to send a provided message content & optional view to the defined endpoint.
    """

    async def send(self, content: str, *, view: View | None = None) -> Any:
        """Send the provided message content & optional view to the defined endpoint."""
        raise NotImplementedError


class ChannelMessageSender(MessageSenderComponent):
    """
    Concrete definition of a channel sending component.

    Defines the way to send a provided message content & optional view to the saved channel.
    """

    def __init__(self, channel: discord.DMChannel | discord.TextChannel) -> None:
        """Initialize a new ChannelMessageSender with the given channel for later use."""
        self.channel: discord.DMChannel | discord.TextChannel = channel

    async def send(self, content: str, *, view: View | None = None) -> Any:
        """Send the provided message content & optional view to the saved channel."""
        class _BaseChannelSendKwargs(TypedDict):
            """Type hint definition for the required kwargs to the channel send function."""

            content: str

        class ChannelSendKwargs(_BaseChannelSendKwargs, total=False):
            """
            Type hint definition for all kwargs to the channel send function.

            Includes both required & optional kwargs.
            """

            view: View

        send_kwargs: ChannelSendKwargs = {"content": content}
        if view:
            send_kwargs["view"] = view

        await self.channel.send(**send_kwargs)


class ResponseMessageSender(MessageSenderComponent):
    """
    Concrete definition of a context-based response sending component.

    Defines the way to send a provided message content & optional view
    to the saved interaction context.
    """

    def __init__(self, ctx: TeXBotApplicationContext) -> None:
        """Initialize a new ResponseMessageSender with the given context for later use."""
        self.ctx: TeXBotApplicationContext = ctx

    async def send(self, content: str, *, view: View | None = None) -> Any:
        """Send the provided message content & optional view to the saved context."""
        await self.ctx.respond(content=content, view=view, ephemeral=True)
