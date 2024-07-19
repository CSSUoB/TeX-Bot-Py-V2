"""Class definitions of components that send provided message content to a defined endpoint."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "MessageSenderComponent",
    "ChannelMessageSender",
    "ResponseMessageSender",
)


import abc
from typing import Final, TypedDict, final, override

import discord
from discord.ui import View

from .tex_bot_contexts import TeXBotApplicationContext


class MessageSenderComponent(abc.ABC):
    """
    Abstract protocol definition of a sending component.

    Defines the way to send a provided message content & optional view to the defined endpoint.
    """

    @override
    def __init__(self) -> None:
        self.sent_message: discord.Message | discord.Interaction | None = None

    @abc.abstractmethod
    async def _send(self, content: str, *, view: View | None = None) -> discord.Message | discord.Interaction:  # noqa: E501
        """
        Subclass implementation of `send()` method.

        Implementations should send the provided message content & optional view
        to the defined endpoint.
        """

    @final
    async def send(self, content: str, *, view: View | None = None) -> None:
        """Send the provided message content & optional view to the defined endpoint."""
        if self.sent_message is not None:
            ALREADY_SENT_MESSAGE: Final[str] = (
                f"A message has already been sent using this {type(self).__name__}Component."
            )
            raise RuntimeError(ALREADY_SENT_MESSAGE)

        self.sent_message = await self._send(content=content, view=view)

    async def delete(self) -> None:
        """Delete the previously sent message."""
        if self.sent_message is None:
            NOT_YET_SENT_MESSAGE: Final[str] = (
                f"No message has been sent yet using this {type(self).__name__}Component."
            )
            raise RuntimeError(NOT_YET_SENT_MESSAGE)

        if isinstance(self.sent_message, discord.Message):
            await self.sent_message.delete()

        else:
            await self.sent_message.delete_original_message()


class ChannelMessageSender(MessageSenderComponent):
    """
    Concrete definition of a channel sending component.

    Defines the way to send a provided message content & optional view to the saved channel.
    """

    @override
    def __init__(self, channel: discord.DMChannel | discord.TextChannel) -> None:
        self.channel: discord.DMChannel | discord.TextChannel = channel

        super().__init__()

    @override
    async def _send(self, content: str, *, view: View | None = None) -> discord.Message | discord.Interaction:  # noqa: E501
        class _BaseChannelSendKwargs(TypedDict):
            """Type-hint-definition for the required kwargs to the channel-send-function."""

            content: str

        class ChannelSendKwargs(_BaseChannelSendKwargs, total=False):
            """
            Type-hint-definition for all kwargs to the channel-send-function.

            Includes both required & optional kwargs.
            """

            view: View

        send_kwargs: ChannelSendKwargs = {"content": content}
        if view:
            send_kwargs["view"] = view

        return await self.channel.send(**send_kwargs)


class ResponseMessageSender(MessageSenderComponent):
    """
    Concrete definition of a context-based response sending component.

    Defines the way to send a provided message content & optional view
    to the saved interaction context.
    """

    @override
    def __init__(self, ctx: TeXBotApplicationContext) -> None:
        self.ctx: TeXBotApplicationContext = ctx

        super().__init__()

    @override
    async def _send(self, content: str, *, view: View | None = None) -> discord.Message | discord.Interaction:  # noqa: E501
        return await self.ctx.respond(content=content, view=view, ephemeral=True)
