import discord

from cogs._utils import TeXBotCog


class SourceCommandCog(TeXBotCog):
    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        description="Displays information about the source code of this bot."
    )
    async def source(self, ctx: discord.ApplicationContext) -> None:
        """Definition & callback response of the "source" command."""
        await ctx.respond(
            (
                "TeX is an open-source project made specifically for the CSS Discord server!"
                " You can see and contribute to the source code at https://github.com/CSSUoB/TeX-Bot-Py-V2"
            ),
            ephemeral=True
        )
