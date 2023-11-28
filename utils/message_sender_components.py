from typing import Any, Protocol, TypedDict

import discord
from discord.ui import View

from utils.tex_bot_contexts import TeXBotApplicationContext


class MessageSenderComponent(Protocol):
    async def send(self, content: str, *, view: View | None = None) -> Any:
        raise NotImplementedError


class ChannelMessageSender(MessageSenderComponent):
    def __init__(self, channel: discord.DMChannel | discord.TextChannel) -> None:
        self.channel: discord.DMChannel | discord.TextChannel = channel

    class _BaseSendKwargs(TypedDict):
        content: str

    class SendKwargs(_BaseSendKwargs, total=False):
        view: View

    async def send(self, content: str, *, view: View | None = None) -> Any:
        send_kwargs: ChannelMessageSender.SendKwargs = {"content": content}
        if view:
            send_kwargs["view"] = view

        await self.channel.send(**send_kwargs)


class ResponseMessageSender(MessageSenderComponent):
    def __init__(self, ctx: TeXBotApplicationContext) -> None:
        self.ctx: TeXBotApplicationContext = ctx

    async def send(self, content: str, *, view: View | None = None) -> Any:
        await self.ctx.respond(content=content, view=view, ephemeral=True)
