"""Contains cog classes for any edit_message interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("EditMessageCommandCog",)


import re
from collections.abc import Set

import discord

from exceptions import DiscordMemberNotInMainGuildError
from exceptions.base import BaseDoesNotExistError
from utils import (
    CommandChecks,
    TeXBotApplicationContext,
    TeXBotAutocompleteContext,
    TeXBotBaseCog,
)


class EditMessageCommandCog(TeXBotBaseCog):
    # noinspection SpellCheckingInspection
    """Cog class that defines the "/edit-message" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_text_channels(ctx: TeXBotAutocompleteContext) -> Set[discord.OptionChoice] | Set[str]:  # noqa: E501
        """
        Autocomplete callable that generates the set of available selectable channels.

        The list of available selectable channels is unique to each member, and is used in any
        of the "edit-message" slash-command options that have a channel input-type.
        """
        if not ctx.interaction.user:
            return set()

        try:
            interaction_user: discord.Member = await ctx.tex_bot.get_main_guild_member(
                ctx.interaction.user,
            )
        except (BaseDoesNotExistError, DiscordMemberNotInMainGuildError):
            return set()

        if not await ctx.tex_bot.check_user_has_committee_role(interaction_user):
            return set()

        return await TeXBotBaseCog.autocomplete_get_text_channels(ctx)

    # noinspection SpellCheckingInspection
    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="edit-message",
        description="Edits a message sent by TeX-Bot to the value supplied.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="channel",
        description="The channel that the message, you wish to edit, is in.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_text_channels),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_channel_id",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="message_id",
        input_type=str,
        description="The ID of the message you wish to edit.",
        required=True,
        max_length=20,
        min_length=17,
        parameter_name="str_message_id",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="text",
        input_type=str,
        description="The new text you want the message to say.",
        required=True,
        max_length=2000,
        min_length=1,
        parameter_name="new_message_content",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def edit_message(self, ctx: TeXBotApplicationContext, str_channel_id: str, str_message_id: str, new_message_content: str) -> None:  # noqa: E501
        """
        Definition & callback response of the "edit_message" command.

        The "write_roles" command edits a message sent by TeX-Bot to the value supplied.
        """
        # NOTE: Shortcut accessors are placed at the top of the function, so that the exceptions they raise are displayed before any further errors may be sent
        main_guild: discord.Guild = self.tex_bot.main_guild

        if not re.match(r"\A\d{17,20}\Z", str_channel_id):
            await self.command_send_error(
                ctx,
                message=f"{str_channel_id!r} is not a valid channel ID.",
            )
            return

        channel_id: int = int(str_channel_id)

        if not re.match(r"\A\d{17,20}\Z", str_message_id):
            await self.command_send_error(
                ctx,
                message=f"{str_message_id!r} is not a valid message ID.",
            )
            return

        message_id: int = int(str_message_id)

        channel: discord.TextChannel | None = discord.utils.get(
            main_guild.text_channels,
            id=channel_id,
        )
        if not channel:
            await self.command_send_error(
                ctx,
                message=f"Text channel with ID \"{channel_id}\" does not exist.",
            )
            return

        try:
            message: discord.Message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await self.command_send_error(
                ctx,
                message=f"Message with ID \"{message_id}\" does not exist.",
            )
            return

        try:
            await message.edit(content=new_message_content)
        except discord.Forbidden:
            await self.command_send_error(
                ctx,
                message=(
                    f"Message with ID {str(message_id)!r} cannot be edited "
                    "because it belongs to another user."
                ),
            )
            return
        else:
            await ctx.respond("Message edited successfully.", ephemeral=True)
