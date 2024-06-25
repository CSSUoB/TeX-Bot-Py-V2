"""Contains cog classes for handover functionality."""


from collections.abc import Sequence

__all__: Sequence[str] = ("HandoverCommandCog", "ResetRolesCommandCog")

import logging
from logging import Logger

import discord

from utils import TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")


class HandoverCommandCog(TeXBotBaseCog):
    """Cog class thaat defines the handover command."""

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="handover",
        description="Initiates the discord handover procedure for new committee",
    )
    async def handover(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "handover" command.

        The "handover" command runs the relavent handover methods
        which will perform the following actions:
        - Give @Committee role to anyone with @Committee-Elect
        - Remove @Committee-Elect from anyone that has it
        - Remove permissions for @Committee-Elect from all channels except #Handover
        """
        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            "Running handover procedures!!",
        )
        logger.debug("Running the handover command!")
        initial_response.edit(content="Done!!")


class ResetRolesCommandCog(TeXBotBaseCog):
    """Cog class that defines the reset_roles command."""

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="reset_roles",
        description="Resets member and year roles",
    )
    async def reset_roles(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "reset_roles" command.

        The "reset_roles" command removes the mmeber role from anyone that has it
        and subsequently calls the method to reset the membership database.
        """
        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            "Running reset roles!!",
        )
        logger.debug("Reset roles command called!")
        initial_response.edit(content="Complete!")

