"""Contains cog classes for any command_success interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("CommandSuccessCog",)


import logging
from logging import Logger

from utils import TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")


class CommandSuccessCog(TeXBotBaseCog):
    """Cog class that defines additional code to execute upon a command success."""

    @TeXBotBaseCog.listener()
    async def on_application_command_completion(self, ctx: TeXBotApplicationContext) -> None:
        logger.debug("Command execution complete.")  # TODO: Pass command name to logger's extra
