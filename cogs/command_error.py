import discord

from cogs._utils import TeXBotCog


class CommandErrorCog(TeXBotCog):
    @TeXBotCog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException) -> None:  # noqa: E501
        """Log any major command errors in the logging channel & stderr."""
        await self.send_error(
            ctx,
            message="Please contact a committee member.",
            logging_message=error
        )
