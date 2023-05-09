import random
import re
import traceback

import discord
from discord import ApplicationContext, Forbidden, Guild, Member, Message, NotFound, OptionChoice, Permissions, Role, TextChannel
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
        guild: Guild = ctx.bot.css_guild  # type: ignore
    except GuildDoesNotExist:
        return set()

    channel_permissions_limiter: Member | Role | None = discord.utils.get(guild.roles, name="@everyone")
    if channel_permissions_limiter is None:
        return set()

    interaction_member: Member | None = await guild.fetch_member(ctx.interaction.user.id)
    if interaction_member:
        channel_permissions_limiter = interaction_member

    return {OptionChoice(name=f"#{channel.name}", value=str(channel.id)) for channel in guild.text_channels if channel.permissions_for(channel_permissions_limiter).is_superset(Permissions(send_messages=True, view_channel=True))}


async def autocomplete_get_members(ctx: discord.AutocompleteContext):
    try:
        guild: Guild = ctx.bot.css_guild  # type: ignore
    except GuildDoesNotExist:
        return set()

    members: set[Member] = {member for member in guild.members if not member.bot}

    try:
        guest_role: Role = ctx.bot.guest_role  # type: ignore
    except RoleDoesNotExist:
        pass
    else:
        members = {member for member in members if guest_role not in member.roles}

    return {OptionChoice(name=f"@{member.name}", value=str(member.id)) for member in members}


async def induct(ctx: discord.ApplicationContext, induction_member: Member, guild: Guild, silent: bool):
    interaction_member: Member | None = await guild.fetch_member(ctx.user.id)
    if interaction_member is None:
        await send_error(
            ctx,
            command_name="induct",
            message="You must be a member of the CSS Discord server to run this command."
        )
        return

    try:
        committee_role: Role = ctx.bot.committee_role  # type: ignore
    except RoleDoesNotExist as committee_role_error:
        await send_error(ctx, error_code="E2001", command_name="induct")
        traceback.print_exception(committee_role_error)
        await ctx.bot.close()
        raise

    if committee_role not in interaction_member.roles:
        await send_error(
            ctx,
            command_name="induct",
            message="You must have the \"Committee\" role to run this command."
        )
        return

    try:
        guest_role: Role = ctx.bot.guest_role  # type: ignore
    except RoleDoesNotExist as guest_role_error:
        await send_error(ctx, error_code="E2002", command_name="induct")
        traceback.print_exception(guest_role_error)
        await ctx.bot.close()
        raise

    if guest_role in induction_member.roles:
        await ctx.respond(
            "ℹ️No changes made. User has already been inducted.ℹ️",
            ephemeral=True
        )
        return

    if induction_member.bot:
        await send_error(
            ctx,
            command_name="induct",
            message=f"Member cannot be inducted because they are a bot."
        )
        return

        if not silent:
            general_channel: TextChannel | None = self.bot.general_channel
            if general_channel is None:
                await self.send_error(
                    ctx,
                    error_code="E1032",
                    command_name="induct",
                    logging_message=str(GeneralChannelDoesNotExist())
                )
                return

            roles_channel_mention: str = "`#roles`"

            roles_channel: TextChannel | None = self.bot.roles_channel
            if roles_channel:
                roles_channel_mention = roles_channel.mention

            await general_channel.send(
                f"""{random.choice(settings["WELCOME_MESSAGES"]).replace("<User>", induction_member.mention).strip()} :tada:\nRemember to grab your roles in {roles_channel_mention} and say hello to everyone here! :wave:"""
            )

        await induction_member.add_roles(
            guest_role,  # type: ignore
            reason=f"{ctx.user} used TeX Bot slash-command: /induct"
        )

        await ctx.respond("User inducted successfully.", ephemeral=True)


async def user_command_induct(ctx: ApplicationContext, member: Member, silent: bool):
    try:
        guild: Guild = ctx.bot.css_guild  # type: ignore
    except GuildDoesNotExist as guild_error:
        await send_error(ctx, error_code="E1001", command_name="induct")
        traceback.print_exception(guild_error)
        await ctx.bot.close()
        raise

    await induct(ctx, member, guild, silent)


        return {OptionChoice(name=f"@{member.name}", value=str(member.id)) for member in members}

    @discord.slash_command(description="Replies with Pong!")
    async def ping(self, ctx: ApplicationContext):
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
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await send_error(ctx, error_code="E1001", command_name="write_roles")
            traceback.print_exception(guild_error)
            await ctx.bot.close()
            raise

        interaction_member: Member | None = await guild.fetch_member(ctx.user.id)
        if interaction_member is None:
            await send_error(
                ctx,
                command_name="write_roles",
                message="You must be a member of the CSS Discord server to run this command."
            )
            return

        try:
            committee_role: Role = self.bot.committee_role
        except RoleDoesNotExist as committee_role_error:
            await send_error(ctx, error_code="E2001", command_name="write_roles")
            traceback.print_exception(committee_role_error)
            await ctx.bot.close()
            raise

        if committee_role not in interaction_member.roles:
            await send_error(
                ctx,
                command_name="write_roles",
                message="You must have the \"Committee\" role to run this command."
            )
            return

        try:
            roles_channel: TextChannel = self.bot.roles_channel
        except ChannelDoesNotExist as roles_channel_error:
            await send_error(ctx, error_code="E3001", command_name="write_roles")
            traceback.print_exception(roles_channel_error)
            await ctx.bot.close()
            raise

        roles_message: str
        for roles_message in settings["ROLES_MESSAGES"]:
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
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await send_error(ctx, error_code="E1001", command_name="edit_message")
            traceback.print_exception(guild_error)
            await ctx.bot.close()
            raise

        channel: TextChannel | None = discord.utils.get(guild.text_channels, id=channel_id)
        if channel is None:
            await send_error(
                ctx,
                command_name="edit_message",
                message=f"Text channel with ID \"{channel_id}\" does not exist."
            )
            return

        interaction_member: Member | None = await guild.fetch_member(ctx.user.id)
        if interaction_member is None:
            await send_error(
                ctx,
                command_name="edit_message",
                message="You must be a member of the CSS Discord server to run this command."
            )
            return

        try:
            committee_role: Role = self.bot.committee_role
        except RoleDoesNotExist as committee_role_error:
            await send_error(ctx, error_code="E2001", command_name="edit_message")
            traceback.print_exception(committee_role_error)
            await ctx.bot.close()
            raise

        if committee_role not in interaction_member.roles:
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

    @discord.slash_command(
        name="induct",
        description="Gives a user the @Guest role, then sends a message in #general saying hello."
    )
    @discord.option(
        name="user",
        description="The user to induct.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_members),
        required=True,
        parameter_name="str_induct_member_id"
    )
    @discord.option(
        name="silent",
        description="Triggers whether a message is sent or not.",
        input_type=bool,
        default=False,
        required=False
    )
    async def slash_command_induct(self, ctx: ApplicationContext, str_induct_member_id: str, silent: bool):
        if not re.match(r"\A\d{17,20}\Z", str_induct_member_id):
            await send_error(
                ctx,
                command_name="induct",
                message=f"\"{str_induct_member_id}\" is not a valid user ID."
            )
            return

        induct_member_id: int = int(str_induct_member_id)

        try:
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await send_error(ctx, error_code="E1001", command_name="induct")
            traceback.print_exception(guild_error)
            await ctx.bot.close()
            raise

        induct_member: Member | None = await guild.fetch_member(induct_member_id)
        if induct_member is None:
            await send_error(
                ctx,
                command_name="induct",
                message=f"Member with ID \"{induct_member_id}\" does not exist."
            )
            return

        await induct(ctx, induct_member, guild, silent)

    @discord.user_command(name="Induct User")
    async def non_silent_user_command_induct(self, ctx: ApplicationContext, member: Member):
        await user_command_induct(ctx, member, silent=False)

    @discord.user_command(name="Silently Induct User")
    async def silent_user_command_induct(self, ctx: ApplicationContext, member: Member):
        await user_command_induct(ctx, member, silent=True)


def setup(bot: TeXBot):
    bot.add_cog(Commands(bot))
