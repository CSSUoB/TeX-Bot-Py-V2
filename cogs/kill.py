"""Contains cog classes for any killing interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("KillCommandCog", "ConfirmKillView")

import contextlib
import logging
from logging import Logger
from typing import Final

import discord
from discord.ui import View

from exceptions import BaseDoesNotExistError
from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Logger = logging.getLogger("TeX-Bot")


class ConfirmKillView(View):
    """A discord.View containing two buttons to confirm shutting down TeX-Bot."""

    @classmethod
    async def _delete_message(cls, response: discord.InteractionResponse) -> None:
        e: discord.NotFound
        try:
            await response.edit_message(delete_after=0)
        except discord.NotFound as e:
            MESSAGE_WAS_ALREADY_DELETED: Final[bool] = (
                e.code == 10008
                or ("unknown" in e.text.lower() and "message" in e.text.lower())
            )
            if not MESSAGE_WAS_ALREADY_DELETED:
                raise e from e

    @discord.ui.button(  # type: ignore[misc]
        label="SHUTDOWN",
        style=discord.ButtonStyle.red,
        custom_id="shutdown_confirm",
    )
    async def confirm_shutdown_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """When the shutdown button is pressed, delete the message."""
        # noinspection PyTypeChecker
        await self._delete_message(interaction.response)

    @discord.ui.button(  # type: ignore[misc]
        label="CANCEL",
        style=discord.ButtonStyle.green,
        custom_id="shutdown_cancel",
    )
    async def cancel_shutdown_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """When the cancel button is pressed, delete the message."""
        # noinspection PyTypeChecker
        await self._delete_message(interaction.response)


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
        with contextlib.suppress(BaseDoesNotExistError):
            committee_role = await self.bot.committee_role

        response: discord.Message | discord.Interaction = await ctx.respond(
            content=(
                f"{f"Hi {committee_role.mention}, a" if committee_role else "A"}"
                "re you sure you want to kill me?\n"
                "This action is irreversible "
                "and will prevent me from performing any further actions.\n\n"
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

        await confirmation_message.delete()

        if button_interaction.data["custom_id"] == "shutdown_confirm":  # type: ignore[index, typeddict-item]
            await button_interaction.respond(
                content="My battery is low and it's getting dark...",
            )
            await self.bot.perform_kill_and_close(initiated_by_user=ctx.interaction.user)
            return

        if button_interaction.data["custom_id"] == "shutdown_cancel":  # type: ignore[index, typeddict-item]
            await button_interaction.respond(
                content="Shutdown has been cancelled.",
            )
            logger.info("Manual shutdown cancelled by %s.", ctx.interaction.user)
            return

        raise ValueError
