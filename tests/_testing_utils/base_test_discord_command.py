from collections.abc import Sequence

__all__: Sequence[str] = ("BaseTestDiscordCommand",)

import abc
import asyncio
from typing import Final

from classproperties import classproperty
from discord import MessageCommand, SlashCommand, UserCommand

from tests._testing_utils import TestingApplicationContext
from utils import TeXBot


class BaseTestDiscordCommand:
    _BOT: TeXBot = TeXBot()

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def COMMAND(cls) -> SlashCommand | UserCommand | MessageCommand:  # noqa: N802,N805
        """"""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def BOT(cls) -> TeXBot:  # noqa: N802,N805
        return cls._BOT

    @classmethod
    def execute_command(cls, ctx: TestingApplicationContext, **kwargs: object) -> None:
        if cls.COMMAND.cog is None:
            COG_NOT_DEFINED_MESSAGE: Final[str] = "Cog is not defined."
            raise ValueError(COG_NOT_DEFINED_MESSAGE)

        asyncio.run(
            cls.COMMAND.callback(  # type: ignore[arg-type,call-arg]
                self=cls.COMMAND.cog(cls.BOT),
                ctx=ctx,
                **kwargs
            )
        )
