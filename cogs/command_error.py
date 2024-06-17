"""Contains cog classes for any command_error interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("CommandErrorCog",)


import contextlib
import logging
from logging import Logger
from typing import Final

import discord
from discord import Forbidden
from discord.ext.commands.errors import CheckAnyFailure

from exceptions import (
    CommitteeRoleDoesNotExistError,
    ErrorCodeCouldNotBeIdentifiedError,
    GuildDoesNotExistError,
    UnknownDjangoError,
)
from exceptions.base import BaseErrorWithErrorCode
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class CommandErrorCog(TeXBotBaseCog):
    """Cog class that defines additional code to execute upon a command error."""

    @classmethod
    def _get_logging_message_from_error(cls, error: discord.ApplicationCommandInvokeError) -> str | None:  # noqa: E501
        if isinstance(error.original, GuildDoesNotExistError):
            return None

        if not str(error.original).strip(". -\"'"):
            return f"{error.original.__class__.__name__} was raised."

        if str(error.original).startswith("\"") or str(error.original).startswith("'"):
            return f"{error.original.__class__.__name__}: {error.original}"

        if isinstance(error.original, UnknownDjangoError):
            return str(error.original)

        if isinstance(error.original, RuntimeError | NotImplementedError):
            return f"{error.original.__class__.__name__}: {error.original}"

        return str(error.original)

    @classmethod
    def _get_error_code_from_error(cls, error: discord.ApplicationCommandInvokeError) -> str:
        if isinstance(error.original, Forbidden):
            return "E1044"

        if isinstance(error.original, BaseErrorWithErrorCode):
            return error.original.ERROR_CODE

        raise ErrorCodeCouldNotBeIdentifiedError(other_error=error.original)

    @TeXBotBaseCog.listener()
    async def on_application_command_error(self, ctx: TeXBotApplicationContext, error: discord.ApplicationCommandError) -> None:  # noqa: E501
        """Log any major command errors in the logging channel & stderr."""
        IS_FATAL: Final[bool] = (
            isinstance(error, discord.ApplicationCommandInvokeError)
            and (
                isinstance(error.original, RuntimeError | NotImplementedError)
                or type(error.original) is Exception
            )
        )

        error_code: str | None = None
        message: str | None = "Please contact a committee member." if not IS_FATAL else ""
        logging_message: str | BaseException | None = None

        if isinstance(error, discord.ApplicationCommandInvokeError):
            logging_message = self._get_logging_message_from_error(error)
            with contextlib.suppress(ErrorCodeCouldNotBeIdentifiedError):
                error_code = self._get_error_code_from_error(error)

        elif isinstance(error, CheckAnyFailure):
            if CommandChecks.is_interaction_user_in_main_guild_failure(error.checks[0]):
                message = (
                    f"You must be a member of the {self.bot.group_short_name} Discord server "
                    "to use this command."
                )

            elif CommandChecks.is_interaction_user_has_committee_role_failure(error.checks[0]):
                # noinspection PyUnusedLocal
                committee_role_mention: str = "@Committee"
                with contextlib.suppress(CommitteeRoleDoesNotExistError):
                    committee_role_mention = (await self.bot.committee_role).mention
                message = f"Only {committee_role_mention} members can run this command."

        await self.command_send_error(
            ctx,
            error_code=error_code,
            message=message,
            logging_message=logging_message,
            is_fatal=IS_FATAL,
        )

        if isinstance(error, discord.ApplicationCommandInvokeError):
            if isinstance(error.original, GuildDoesNotExistError):
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
                            (
                                f"({command_name})"
                                if command_name in self.ERROR_ACTIVITIES
                                else ""
                            ),
                            str(error.original).rstrip(".:"),
                        )
                        if message_part
                    ),
                )

            BOT_NEEDS_CLOSING: Final[bool] = (
                isinstance(
                    error.original,
                    RuntimeError | NotImplementedError | GuildDoesNotExistError,
                )
                or type(error.original) is Exception
            )
            if BOT_NEEDS_CLOSING:
                await self.bot.close()
