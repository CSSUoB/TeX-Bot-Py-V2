"""Contains cog classes for any command_error interactions."""

import contextlib
import logging

import discord
from discord.ext.commands import CheckAnyFailure

from cogs._checks import Checks
from cogs._utils import TeXBotApplicationContext, TeXBotCog
from exceptions import (
    BaseDoesNotExistError,
    EveryoneRoleCouldNotBeRetrieved,
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

        if isinstance(error, discord.ApplicationCommandInvokeError) and isinstance(error.original, BaseDoesNotExistError | EveryoneRoleCouldNotBeRetrieved):  # noqa: E501
            message = None
            error_code = error.original.ERROR_CODE
            logging_message = None if isinstance(error, GuildDoesNotExist) else error.original

        elif isinstance(error, CheckAnyFailure):
            if error.checks[0] == Checks.check_interaction_user_in_css_guild:
                message = "You must be a member of the CSS Discord server to use this command."

            elif error.checks[0] == Checks.check_interaction_user_has_committee_role:
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

        if isinstance(error, GuildDoesNotExist):
            # TODO: Use ctx.command for stacktrace
            logging.critical(error, exc_info=NotImplementedError())
            await self.bot.close()
