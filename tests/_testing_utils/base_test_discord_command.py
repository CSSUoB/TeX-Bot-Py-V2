from collections.abc import Sequence

__all__: Sequence[str] = ("BaseTestDiscordCommand",)

import abc
import asyncio
from typing import Final

from classproperties import classproperty
from discord import MessageCommand, SlashCommand, UserCommand

from tests._testing_utils.pycord_internals import TestingApplicationContext


class BaseTestDiscordCommand:
    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def COMMAND(cls) -> SlashCommand | UserCommand | MessageCommand:  # noqa: N802,N805
        """"""

    @classmethod
    def execute_command(cls, ctx: TestingApplicationContext, **kwargs: object) -> None:
        if cls.COMMAND.cog is None:
            COG_NOT_DEFINED_MESSAGE: Final[str] = "Cog is not defined."
            raise ValueError(COG_NOT_DEFINED_MESSAGE)

        asyncio.new_event_loop().run_until_complete(
            cls.COMMAND.callback(  # type: ignore[arg-type,call-arg]
                self=cls.COMMAND.cog,
                ctx=ctx,
                **kwargs
            )
        )
