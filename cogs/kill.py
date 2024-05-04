"""Contains cog classes for any killing interactions."""

import logging
from collections.abc import Sequence
from logging import Logger

import discord

from utils import CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

__all__: Sequence[str] = ("KillCommandCog","ConfirmationView")

logger: Logger = logging.getLogger("TeX-Bot")

class ConfirmationView(discord.ui.View):
    """Confirmation view for the kill command."""

    @discord.ui.button( # type: ignore[misc]
        label = "SHUTDOWN",
        style = discord.ButtonStyle.red,
        custom_id = "shutdown",
    )
    async def shutdown_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """When the shutdown button is pressed, delete the message."""
        await interaction.response.edit_message(delete_after = 0)

    @discord.ui.button( # type: ignore[misc]
        label = "CANCEL",
        style = discord.ButtonStyle.green,
        custom_id = "cancel",
    )
    async def cancel_button_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:  # noqa: E501
        """When the cancel button is pressed, delete the message."""
        await interaction.response.edit_message(delete_after = 0)


class KillCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/kill" command."""

    async def confirm_kill(self, ctx: TeXBotApplicationContext) -> None:
        """Confirm that the user did indeed intent to kill the bot."""
        main_guild = self.bot.main_guild
        confirmation_message_channel: discord.TextChannel = main_guild.get_channel(1128049192498102483) # noqa: E501
        committee_role: discord.Role = await self.bot.committee_role

        confirmation_message: discord.Message = await confirmation_message_channel.send(
            content = (
            f"""Hi {committee_role.mention}, are you sure you want to kill me?\n"""
            """This action is irreversible and will prevent me from performing any actions.\n"""  # noqa: E501
            """Please confirm your choice by clicking the button below.\n"""
            f"""This action was triggered by {ctx.interaction.user.mention}.\n"""
            ), view = ConfirmationView())

        button_interaction: discord.Interaction = await self.bot.wait_for(
            "interaction",
            check=lambda interaction: (
                interaction.type == discord.InteractionType.component
                and interaction.message == confirmation_message
                and committee_role in interaction.user.roles
            ),
        )

        if button_interaction.component.custom_id == "shutdown":
            await confirmation_message.delete()
            _: discord.Message = await confirmation_message_channel.send(
                content = "My battery is low and it's getting dark...",
            )
            logger.info("Manual shutdown initiated by %s.", ctx.interaction.user)
            await self.bot.close()

        elif button_interaction.component.custom_id == "cancel":
            await confirmation_message.delete()
            await confirmation_message_channel.send(
                content = "Shutdown has been cancelled.",
            )
            logger.info("Manual shutdown cancelled by %s.", ctx.interaction.user)

    @discord.slash_command( # type: ignore[no-untyped-call, misc]
        name="kill",
        description=("Kills the bot."),
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def kill(self, ctx: TeXBotApplicationContext) -> None:
        """Kills the bot."""
        await self.confirm_kill(ctx)
