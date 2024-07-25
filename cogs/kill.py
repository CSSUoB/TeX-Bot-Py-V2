"""Contains cog classes for any killing interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("KillCommandCog", "ConfirmKillView")


import contextlib
import logging
from logging import Logger
from typing import Final

import discord
from discord.ui import View

from exceptions import CommitteeRoleDoesNotExistError
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class ConfirmKillView(View):
    """A discord.View containing two buttons to confirm shutting down TeX-Bot."""

    @discord.ui.button(  # type: ignore[misc]
        label="SHUTDOWN",
        style=discord.ButtonStyle.red,
        custom_id="shutdown_confirm",
    )
    async def confirm_shutdown_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """When the shutdown button is pressed, delete the message."""
        logger.debug("\"Confirm\" button pressed. %s", interaction)

    @discord.ui.button(  # type: ignore[misc]
        label="CANCEL",
        style=discord.ButtonStyle.grey,
        custom_id="shutdown_cancel",
    )
    async def cancel_shutdown_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """When the cancel button is pressed, delete the message."""
        logger.debug("\"Cancel\" button pressed. %s", interaction)


class KillCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/kill" command and its call-back method."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="kill",
        description="Shutdown TeX-Bot.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def kill(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "kill" command.

        The "kill" command shuts down TeX-Bot,
        but only after the user has confirmed that this is the action they wish to take.
        """
        committee_role: discord.Role | None = None
        with contextlib.suppress(CommitteeRoleDoesNotExistError):
            committee_role = await self.bot.committee_role

        response: discord.Message | discord.Interaction = await ctx.respond(
            content=(
                f"{f"Hi {committee_role.mention}, a" if committee_role else "A"}"
                "re you sure you want to kill me?\n"
                "This action is irreversible "
                "and will prevent me from performing any further actions "
                "until I am manually restarted.\n\n"
                "Please confirm using the buttons below."
            ),
            view=ConfirmKillView(),
        )
        confirmation_message: discord.Message = (
            response
            if isinstance(response, discord.Message)
            else await response.original_response()
        )

        button_interaction: discord.Interaction = await self.bot.wait_for(
            "interaction",
            check=lambda interaction: (
                interaction.type == discord.InteractionType.component
                and interaction.message.id == confirmation_message.id
                and ((committee_role in interaction.user.roles) if committee_role else True)
                and "custom_id" in interaction.data
                and interaction.data["custom_id"] in {"shutdown_confirm", "shutdown_cancel"}
            ),
        )

        match button_interaction.data["custom_id"]:  # type: ignore[index, typeddict-item]
            case "shutdown_confirm":
                await confirmation_message.edit(
                    content="My battery is low and it's getting dark...",
                    view=None,
                )
                await self.bot.perform_kill_and_close(
                    initiated_by_user=ctx.interaction.user,
                )

            case "shutdown_cancel":
                await confirmation_message.edit(
                    content="Shutdown has been cancelled.",
                    view=None,
                )
                logger.info(
                    "Manual shutdown cancelled by %s.",
                    ctx.interaction.user,
                )

            case _:
                raise ValueError
