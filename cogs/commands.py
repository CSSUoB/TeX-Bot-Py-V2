import logging
import random
import re

import discord
from discord import ApplicationContext, Forbidden, Member, Message, NotFound, OptionChoice, Permissions, Role, TextChannel
from discord.ext import commands

from exceptions import ChannelDoesNotExist, GuildDoesNotExist, RoleDoesNotExist
from main import TeXBot
from setup import settings


async def send_error(ctx: ApplicationContext, error_code: str | None = None, command_name: str | None = None, message: str | None = None):
    construct_error_message: str = "⚠️There was an error"

    if error_code:
        construct_error_message = f"**Contact TeX bot administrator, referencing error code: {error_code}**\n" + construct_error_message

    if command_name:
        construct_error_message += f" when trying to {Commands.ERROR_ACTIVITIES[command_name]}"

    if message:
        construct_error_message += ":"
    else:
        construct_error_message += "."

    construct_error_message += "⚠️"

    if message:
        construct_error_message += f"\n`{message.strip()}`"

    await ctx.respond(construct_error_message, ephemeral=True)


async def autocomplete_get_channels(ctx: discord.AutocompleteContext):
    if ctx.interaction.user is None:
        return set()

    try:
        guild = ctx.bot.css_guild  # type: ignore
    except GuildDoesNotExist:
        return set()

    channel_permissions_limiter: Member | Role | None = discord.utils.get(guild.roles, name="@everyone")
    if channel_permissions_limiter is None:
        return set()

    guild_member: Member | None = await guild.fetch_member(ctx.interaction.user.id)
    if guild_member:
        channel_permissions_limiter = guild_member

    return {OptionChoice(name=f"#{channel.name}", value=str(channel.id)) for channel in guild.text_channels if channel.permissions_for(channel_permissions_limiter).is_superset(Permissions(send_messages=True, view_channel=True))}


class Commands(commands.Cog):
    ROLES_MESSAGES: tuple[str, str, str, str] = (
        "\nReact to this message to get pronoun roles\n🇭 - He/Him\n🇸 - She/Her\n🇹 - They/Them",
        "_ _\nReact to this message to get year group roles\n0️⃣ - Foundation Year\n1️⃣ - First Year\n2️⃣ - Second Year\n🇫 - Final Year (incl. 3rd Year MSci/MEng)\n🇮 - Year in Industry\n🇦 - Year Abroad\n🇹 - Post-Graduate Taught (Masters/MSc) \n🇷 - Post-Graduate Research (PhD) \n🅰️ - Alumnus\n🇩 - Postdoc",
        "_ _\nReact to this message to join the **opt in channels**\n💬 - Serious Talk\n🏡 - Housing\n🎮 - Gaming\n📺 - Anime\n⚽ - Sport\n💼 - Industry\n⛏️ - Minecraft\n🌐 - CSS Website\n🔖 - Archivist",
        "_ _\nReact to this message to opt in to News notifications\n🔈- Get notifications when we `@News`\n🔇- Don't get notifications when we `@News`\n_ _\n> We will still use `@everyone` messages if there is something urgent",
    )
    ERROR_ACTIVITIES = {
        "ping": "reply with Pong!!",
        "write_roles": "send messages",
        "edit_message": "edit the message"
    }

    def __init__(self, bot: TeXBot):
        self.bot: TeXBot = bot

    @discord.slash_command(description="Replies with Pong!")
    async def ping(self, ctx: ApplicationContext):
        logging.warning(f"{ctx.interaction.user} made me pong!!")

        await ctx.respond(
            random.choices(
                [
                    "Pong!",
                    "64 bytes from TeX: icmp_seq=1 ttl=63 time=0.01 ms"
                ],
                weights=settings["PING_COMMAND_EASTER_EGG_WEIGHTS"]
            )[0]
        )

    @discord.slash_command(description="Displays information about the source code of this bot.")
    async def source(self, ctx: ApplicationContext):
        await ctx.respond(
            "TeX is an open-source project made specifically for the CSS Discord! You can see and contribute to the source code at https://github.com/CSSUoB/TeX-Bot-Py"
        )

    # noinspection SpellCheckingInspection
    @discord.slash_command(
        name="writeroles",
        description="Populates #roles with the correct messages."
    )
    async def write_roles(self, ctx: ApplicationContext):
        try:
            guild = self.bot.css_guild
        except GuildDoesNotExist:
            await send_error(ctx, error_code="E1001", command_name="write_roles")
            raise

        guild_member: Member | None = await guild.fetch_member(ctx.user.id)
        if guild_member is None:
            await send_error(
                ctx,
                command_name="write_roles",
                message="You must be a member of the CSS Discord server to run this command."
            )
            return

        try:
            committee_role = self.bot.committee_role
        except RoleDoesNotExist:
            await send_error(ctx, error_code="E1002", command_name="write_roles")
            raise

        if committee_role not in guild_member.roles:
            await send_error(
                ctx,
                command_name="write_roles",
                message="You must have the \"Committee\" role to run this command."
            )
            return

        try:
            roles_channel = self.bot.roles_channel
        except ChannelDoesNotExist:
            await send_error(ctx, error_code="E1003", command_name="write_roles")
            raise

        roles_message: str
        for roles_message in self.ROLES_MESSAGES:
            await roles_channel.send(roles_message)

        await ctx.respond("All messages sent successfully.", ephemeral=True)

    # noinspection SpellCheckingInspection
    @discord.slash_command(
        name="editmessage",
        description="Edits a message sent by TeX to the message supplied."
    )
    @discord.option(
        name="channel",
        description="The channel that the message, you wish to edit, is in.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_channels),
        required=True,
        parameter_name="str_channel_id"
    )
    @discord.option(
        name="message_id",
        input_type=str,
        description="The ID of the message you wish to edit.",
        required=True,
        max_length=20,
        min_length=17,
        parameter_name="str_message_id"
    )
    @discord.option(
        name="text",
        input_type=str,
        description="The new text you want the message to say.",
        required=True,
        max_length=2000,
        min_length=1,
        parameter_name="new_message_content"
    )
    async def edit_message(self, ctx: ApplicationContext, str_channel_id: str, str_message_id: str, new_message_content: str):
        if not re.match(r"\A\d{17,20}\Z", str_channel_id):
            await send_error(
                ctx,
                command_name="edit_message",
                message=f"\"{str_channel_id}\" is not a valid channel ID."
            )
            return

        channel_id: int = int(str_channel_id)

        if not re.match(r"\A\d{17,20}\Z", str_message_id):
            await send_error(
                ctx,
                command_name="edit_message",
                message=f"\"{str_message_id}\" is not a valid message ID."
            )
            return

        message_id: int = int(str_message_id)

        try:
            guild = self.bot.css_guild
        except GuildDoesNotExist:
            await send_error(ctx, error_code="E1001", command_name="edit_message")
            raise

        channel: TextChannel | None = discord.utils.get(guild.text_channels, id=channel_id)
        if channel is None:
            await send_error(
                ctx,
                command_name="edit_message",
                message=f"Text channel with ID \"{channel_id}\" does not exist."
            )
            return

        guild_member: Member | None = await guild.fetch_member(ctx.user.id)
        if guild_member is None:
            await send_error(
                ctx,
                command_name="edit_message",
                message="You must be a member of the CSS Discord server to run this command."
            )
            return

        try:
            committee_role = self.bot.committee_role
        except RoleDoesNotExist:
            await send_error(ctx, error_code="E1002", command_name="edit_message")
            raise

        if committee_role not in guild_member.roles:
            await send_error(
                ctx,
                command_name="edit_message",
                message="You must have the \"Committee\" role to run this command."
            )
            return

        try:
            message: Message = await channel.fetch_message(message_id)
        except NotFound:
            await send_error(
                ctx,
                command_name="edit_message",
                message=f"Message with ID \"{message_id}\" does not exist."
            )
            return

        try:
            await message.edit(content=new_message_content)
        except Forbidden:
            await send_error(
                ctx,
                command_name="edit_message",
                message=f"Message with ID \"{message_id}\" cannot be edited because it belongs to another user."
            )
            return
        else:
            await ctx.respond("Message edited successfully.", ephemeral=True)


def setup(bot: TeXBot):
    bot.add_cog(Commands(bot))
