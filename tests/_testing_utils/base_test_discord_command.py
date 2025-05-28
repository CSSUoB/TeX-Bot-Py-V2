from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final

__all__: "Sequence[str]" = ("BaseTestDiscordCommand",)

import abc
import asyncio
from typing import TYPE_CHECKING

import discord
import pytest
from discord import HTTPClient
from discord.state import ConnectionState
from typed_classproperties import classproperty

from tests._testing_utils.pycord_internals import TestingApplicationContext, TestingInteraction
from utils import TeXBot

if TYPE_CHECKING:
    from discord import MessageCommand, SlashCommand, UserCommand


class BaseTestDiscordCommand:
    @classproperty
    @abc.abstractmethod
    def COMMAND(cls) -> "SlashCommand | UserCommand | MessageCommand":  # noqa: N802
        """The Discord command the cog, linked to this test case, has the functionality for."""

    @classmethod
    def execute_command(cls, ctx: TestingApplicationContext, **kwargs: object) -> None:
        if cls.COMMAND.cog is None:
            COG_NOT_DEFINED_MESSAGE: Final[str] = "Cog is not defined."
            raise ValueError(COG_NOT_DEFINED_MESSAGE)

        asyncio.new_event_loop().run_until_complete(
            cls.COMMAND.callback(  # type: ignore[arg-type,call-arg]
                self=cls.COMMAND.cog,
                ctx=ctx,
                **kwargs,
            ),
        )

    @pytest.fixture(autouse=True)
    def CONTEXT(self) -> TestingApplicationContext:  # noqa: N802
        bot: TeXBot = TeXBot()

        interaction: TestingInteraction = TestingInteraction(
            data={
                "id": 1,
                "application_id": 1,
                "type": discord.InteractionType.application_command.value,
                "token": "1",
                "version": 2,
                "entitlements": [],
            },
            state=ConnectionState(
                dispatch=(lambda: None),
                handlers={},
                hooks={},
                http=HTTPClient(),
                loop=asyncio.new_event_loop(),
            ),
        )

        context: TestingApplicationContext = TestingApplicationContext(bot, interaction)

        context.command = self.COMMAND

        return context
