"""Contains cog classes for any edit_message interactions."""

import logging
import re

import discord

from cogs._utils import TeXBotCog
from exceptions import CommitteeRoleDoesNotExist, GuildDoesNotExist


class EditMessageCommandCog(TeXBotCog):
    # noinspection SpellCheckingInspection
    """Cog class that defines the "/editmessage" command and its call-back method."""

    # noinspection SpellCheckingInspection
    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="editmessage",
        description="Edits a message sent by TeX-Bot to the value supplied."
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="channel",
        description="The channel that the message, you wish to edit, is in.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(
            TeXBotCog.autocomplete_get_text_channels  # type: ignore[arg-type]
        ),
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
    async def edit_message(self, ctx: discord.ApplicationContext, str_channel_id: str, str_message_id: str, new_message_content: str) -> None:  # noqa: E501
        """
        Definition & callback response of the "edit_message" command.

        The "write_roles" command edits a message sent by TeX-Bot to the value supplied.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(ctx, error_code="E1011")
            logging.critical(guild_error)
            await self.bot.close()
            return

        committee_role: discord.Role | None = await self.bot.committee_role
        if not committee_role:
            await self.send_error(
                ctx,
                error_code="E1021",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        if committee_role not in interaction_member.roles:
            committee_role_mention: str = "@Committee"
            if ctx.guild:
                committee_role_mention = committee_role.mention

            await self.send_error(
                ctx,
                message=f"Only {committee_role_mention} members can run this command."
            )
            return

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
            guild.text_channels,
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
                    f"Message with ID \"{message_id}\" cannot be edited because it belongs to"
                    " another user."
                )
            )
            return
        else:
            await ctx.respond("Message edited successfully.", ephemeral=True)
