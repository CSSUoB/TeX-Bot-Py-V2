"""Contains cog classes for any command_error interactions."""

import contextlib
import logging

import discord
from discord.ext.commands import CheckAnyFailure

from cogs._command_checks import Checks
from cogs._utils import TeXBotApplicationContext, TeXBotCog
from exceptions import (
    BaseDoesNotExistError,
    BaseErrorWithErrorCode,
    GuildDoesNotExist,
)


class CommandErrorCog(TeXBotCog):
    """Cog class that defines additional code to execute upon a command error."""

    @TeXBotCog.listener()
    async def on_application_command_error(self, ctx: TeXBotApplicationContext, error: discord.ApplicationCommandError) -> None:  # noqa: E501
        """Log any major command errors in the logging channel & stderr."""
        error_code: str | None = None
        message: str | None = "Please contact a committee member."
        logging_message: str | BaseException | None = None

        if isinstance(error, discord.ApplicationCommandInvokeError) and isinstance(error.original, BaseErrorWithErrorCode):  # noqa: E501
            message = None
            error_code = error.original.ERROR_CODE
            logging_message = (
                None if isinstance(error.original, GuildDoesNotExist) else error.original
            )

        elif isinstance(error, CheckAnyFailure):
            if error.checks[0] == Checks.check_interaction_user_in_css_guild:  # type: ignore[comparison-overlap]
                message = "You must be a member of the CSS Discord server to use this command."

            elif error.checks[0] == Checks.check_interaction_user_has_committee_role:  # type: ignore[comparison-overlap]
                # noinspection PyUnusedLocal
                committee_role_mention: str = "@Committee"
                with contextlib.suppress(BaseDoesNotExistError):
                    committee_role_mention = (await self.bot.committee_role).mention
                message = f"Only {committee_role_mention} members can run this command."

        await self.send_error(
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
            logging.critical(
                " ".join(
                    message_part
                    for message_part
                    in (
                        error.original.ERROR_CODE,
                        f"({command_name})" if command_name in self.ERROR_ACTIVITIES else "",
                        str(error.original)
                    )
                    if message_part
                )
            )
            await self.bot.close()
