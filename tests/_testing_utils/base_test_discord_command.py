from collections.abc import Sequence

__all__: Sequence[str] = ("BaseTestDiscordCommand",)

import abc
import asyncio
from typing import Final

import discord
import pytest
from classproperties import classproperty
from discord import HTTPClient, MessageCommand, SlashCommand, UserCommand
from discord.state import ConnectionState

from tests._testing_utils.pycord_internals import TestingApplicationContext, TestingInteraction
from utils import TeXBot


class BaseTestDiscordCommand:
    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def COMMAND(cls) -> SlashCommand | UserCommand | MessageCommand:  # noqa: N802,N805
        """The Discord command the cog, linked to this test case, has the functionality for."""  # noqa: D401

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

    # noinspection PyPep8Naming
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
