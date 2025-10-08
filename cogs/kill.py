"""Contains cog classes for any killing interactions."""

import logging
from typing import TYPE_CHECKING

import discord
from discord.ui import View

from exceptions import CommitteeRoleDoesNotExistError
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext

__all__: Sequence[str] = ("ConfirmKillView", "KillCommandCog")


logger: Final[Logger] = logging.getLogger("TeX-Bot")


class ConfirmKillView(View):
    """A discord.View containing two buttons to confirm shutting down TeX-Bot."""

    @discord.ui.button(
        label="SHUTDOWN", style=discord.ButtonStyle.red, custom_id="shutdown_confirm"
    )
    async def confirm_shutdown_button_callback(  # type: ignore[misc]
        self, _: discord.Button, interaction: discord.Interaction
    ) -> None:
        """When the shutdown button is pressed, delete the message."""
        logger.debug('"Confirm" button pressed. %s', interaction)

    @discord.ui.button(
        label="CANCEL", style=discord.ButtonStyle.grey, custom_id="shutdown_cancel"
    )
    async def cancel_shutdown_button_callback(  # type: ignore[misc]
        self, _: discord.Button, interaction: discord.Interaction
    ) -> None:
        """When the cancel button is pressed, delete the message."""
        logger.debug('"Cancel" button pressed. %s', interaction)


class KillCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/kill" command and its call-back method."""

    @discord.slash_command(name="kill", description="Shutdown TeX-Bot.")
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def kill(self, ctx: TeXBotApplicationContext) -> None:
        """
        Definition & callback response of the "kill" command.

        The "kill" command shuts down TeX-Bot,
        but only after the user has confirmed that this is the action they wish to take.
        """
        committee_role: discord.Role | None
        try:
            committee_role = await self.bot.committee_role
        except CommitteeRoleDoesNotExistError:
            committee_role = None

        response: discord.Message | discord.Interaction = await ctx.respond(
            content=(
                f"{f'Hi {committee_role.mention}, a' if committee_role else 'A'}"
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
                interaction.type == discord.InteractionType.component  # noqa: CAR180
                and interaction.message.id == confirmation_message.id
                and ((committee_role in interaction.user.roles) if committee_role else True)
                and "custom_id" in interaction.data
                and interaction.data["custom_id"] in {"shutdown_confirm", "shutdown_cancel"}
            ),
        )

        if button_interaction.data["custom_id"] == "shutdown_confirm":  # type: ignore[index, typeddict-item]
            await confirmation_message.edit(
                content="My battery is low and it's getting dark...",
                view=None,
            )
            await self.bot.perform_kill_and_close(initiated_by_user=ctx.interaction.user)

        if button_interaction.data["custom_id"] == "shutdown_cancel":  # type: ignore[index, typeddict-item]
            await confirmation_message.edit(content="Shutdown has been cancelled.", view=None)
            logger.info("Manual shutdown cancelled by %s.", ctx.interaction.user)
            return

        raise ValueError
