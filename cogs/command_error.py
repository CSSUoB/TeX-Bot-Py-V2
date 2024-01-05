"""Contains cog classes for any command_error interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("CommandErrorCog",)

import contextlib
import logging
from logging import Logger

import discord
from discord import Forbidden
from discord.ext.commands import CheckAnyFailure

from exceptions import (
    BaseDoesNotExistError,
    BaseErrorWithErrorCode,
    GuildDoesNotExist,
)
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("texbot")


class CommandErrorCog(TeXBotBaseCog):
    """Cog class that defines additional code to execute upon a command error."""

    @TeXBotBaseCog.listener()
    async def on_application_command_error(self, ctx: TeXBotApplicationContext, error: discord.ApplicationCommandError) -> None:  # noqa: E501
        """Log any major command errors in the logging channel & stderr."""
        error_code: str | None = None
        message: str | None = "Please contact a committee member."
        logging_message: str | BaseException | None = None

        if isinstance(error, discord.ApplicationCommandInvokeError):
            message = None
            logging_message = (
                None if isinstance(error.original, GuildDoesNotExist) else error.original
            )

            if isinstance(error.original, Forbidden):
                error_code = "E1044"

            elif isinstance(error.original, BaseErrorWithErrorCode):
                error_code = error.original.ERROR_CODE

        elif isinstance(error, CheckAnyFailure):
            if CommandChecks.is_interaction_user_in_main_guild_failure(error.checks[0]):
                message = (
                    f"You must be a member of the {self.bot.group_short_name} Discord server "
                    "to use this command."
                )

            elif CommandChecks.is_interaction_user_has_committee_role_failure(error.checks[0]):
                # noinspection PyUnusedLocal
                committee_role_mention: str = "@Committee"
                with contextlib.suppress(BaseDoesNotExistError):
                    committee_role_mention = (await self.bot.committee_role).mention
                message = f"Only {committee_role_mention} members can run this command."

        await self.command_send_error(
            ctx,
            error_code=error_code,
            message=message,
            logging_message=logging_message
        )

        if isinstance(error, discord.ApplicationCommandInvokeError) and isinstance(error.original, GuildDoesNotExist):  # noqa: E501
            command_name: str = (
                ctx.command.callback.__name__
                if (hasattr(ctx.command, "callback")
                    and not ctx.command.callback.__name__.startswith("_"))
                else ctx.command.qualified_name
            )
            logger.critical(
                " ".join(
                    message_part
                    for message_part
                    in (
                        error.original.ERROR_CODE,
                        f"({command_name})" if command_name in self.ERROR_ACTIVITIES else "",
                        str(error.original).rstrip(".:")
                    )
                    if message_part
                )
            )
            await self.bot.close()
