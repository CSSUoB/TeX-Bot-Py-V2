"""Contains cog classes for any edit_message interactions."""

import re

import discord
from discord.ext import commands

from cogs._command_checks import Checks
from cogs._utils import TeXBotApplicationContext, TeXBotAutocompleteContext, TeXBotCog
from exceptions import BaseDoesNotExistError, UserNotInCSSDiscordServer


class EditMessageCommandCog(TeXBotCog):
    # noinspection SpellCheckingInspection
    """Cog class that defines the "/editmessage" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_text_channels(ctx: TeXBotAutocompleteContext) -> set[discord.OptionChoice]:  # noqa: E501
        """
        Autocomplete callable that generates the set of available selectable channels.

        The list of available selectable channels is unique to each member, and is used in any
        of the "edit-message" slash-command options that have a channel input-type.
        """
        if not ctx.interaction.user:
            return set()

        try:
            interaction_user: discord.Member = await ctx.bot.get_css_user(ctx.interaction.user)
            assert await ctx.bot.check_user_has_committee_role(interaction_user)
        except (AssertionError, BaseDoesNotExistError, UserNotInCSSDiscordServer):
            return set()

        return await TeXBotCog.autocomplete_get_text_channels(ctx)

    # noinspection SpellCheckingInspection
    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="editmessage",
        description="Edits a message sent by TeX-Bot to the value supplied."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="channel",
        description="The channel that the message, you wish to edit, is in.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_text_channels),  # type: ignore[arg-type]
        required=True,
        parameter_name="str_channel_id"
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="message_id",
        input_type=str,
        description="The ID of the message you wish to edit.",
        required=True,
        max_length=20,
        min_length=17,
        parameter_name="str_message_id"
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="text",
        input_type=str,
        description="The new text you want the message to say.",
        required=True,
        max_length=2000,
        min_length=1,
        parameter_name="new_message_content"
    )
    @commands.check_any(commands.check(Checks.check_interaction_user_in_css_guild))  # type: ignore[arg-type]
    @commands.check_any(commands.check(Checks.check_interaction_user_has_committee_role))  # type: ignore[arg-type]
    async def edit_message(self, ctx: TeXBotApplicationContext, str_channel_id: str, str_message_id: str, new_message_content: str) -> None:  # noqa: E501
        """
        Definition & callback response of the "edit_message" command.

        The "write_roles" command edits a message sent by TeX-Bot to the value supplied.
        """
        css_guild: discord.Guild = self.bot.css_guild

        if not re.match(r"\A\d{17,20}\Z", str_channel_id):
            await self.send_error(
                ctx,
                message=f"\"{str_channel_id}\" is not a valid channel ID."
            )
            return

        channel_id: int = int(str_channel_id)

        if not re.match(r"\A\d{17,20}\Z", str_message_id):
            await self.send_error(
                ctx,
                message=f"\"{str_message_id}\" is not a valid message ID."
            )
            return

        message_id: int = int(str_message_id)

        channel: discord.TextChannel | None = discord.utils.get(
            css_guild.text_channels,
            id=channel_id
        )
        if not channel:
            await self.send_error(
                ctx,
                message=f"Text channel with ID \"{channel_id}\" does not exist."
            )
            return

        try:
            message: discord.Message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await self.send_error(
                ctx,
                message=f"Message with ID \"{message_id}\" does not exist."
            )
            return

        try:
            await message.edit(content=new_message_content)
        except discord.Forbidden:
            await self.send_error(
                ctx,
                message=(
                    f"Message with ID \"{message_id}\" cannot be edited because it belongs to "
                    "another user."
                )
            )
            return
        else:
            await ctx.respond("Message edited successfully.", ephemeral=True)
