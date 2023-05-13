import logging
import random
import re
import time
from datetime import datetime
from django.utils import timezone

import aiohttp
import discord
import parsedatetime  # type: ignore
from bs4 import BeautifulSoup
from discord import ApplicationContext, Forbidden, Guild, Member, Message, NotFound, OptionChoice, Permissions, Role, TextChannel
from django.core.exceptions import ValidationError  # type: ignore

from db.core.models import Discord_Reminder, Interaction_Reminder_Opt_Out_Member, UoB_Made_Member
from exceptions import CommitteeRoleDoesNotExist, GeneralChannelDoesNotExist, GuestRoleDoesNotExist, GuildDoesNotExist, MemberRoleDoesNotExist, RolesChannelDoesNotExist
from setup import settings
from utils import TeXBot
from cogs.utils import Bot_Cog


class Application_Commands_Cog(Bot_Cog):
    ERROR_ACTIVITIES: dict[str, str] = {
        "ping": "reply with Pong!!",
        "write_roles": "send messages",
        "edit_message": "edit the message",
        "induct": "induct user",
        "make_member": "make you a member",
        "remind_me": "remind you"
    }

    async def send_error(self, ctx: ApplicationContext, error_code: str | None = None, command_name: str | None = None, message: str | None = None, logging_message: str | None = None):
        construct_error_message: str = ":warning:There was an error"
        construct_logging_error_message: str = ""

        if error_code:
            committee_mention: str = "committee"

            committee_role: Role | None = self.bot.committee_role
            if committee_role:
                committee_mention = committee_role.mention

            construct_error_message = f"**Contact a {committee_mention} member, referencing error code: {error_code}**\n" + construct_error_message

            construct_logging_error_message += f"{error_code} :"

        if command_name:
            construct_error_message += f" when trying to {self.ERROR_ACTIVITIES[command_name]}"

            construct_logging_error_message += f" ({command_name})"

        if message:
            construct_error_message += ":"
        else:
            construct_error_message += "."

        construct_error_message += ":warning:"

        if message:
            message = re.sub(r"<@[&#]?\d+>", lambda match: f"`{match.group(0)}`", message.strip())
            construct_error_message += f"\n`{message}`"

        await ctx.respond(construct_error_message, ephemeral=True)

        if logging_message:
            logging.error(f"{construct_logging_error_message} {logging_message}")

    async def _induct(self, ctx: discord.ApplicationContext, induction_member: Member, guild: Guild, silent: bool):
        interaction_member: Member | None = guild.get_member(ctx.user.id)
        if interaction_member is None:
            # noinspection SpellCheckingInspection
            await self.send_error(
                ctx,
                command_name="induct",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        committee_role: Role | None = self.bot.committee_role
        if committee_role is None:
            await self.send_error(
                ctx,
                error_code="E1021",
                command_name="induct",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        if committee_role not in interaction_member.roles:
            await self.send_error(
                ctx,
                command_name="induct",
                message=f"Only {committee_role.mention} members can run this command."
            )
            return

        guest_role: Role | None = self.bot.guest_role
        if guest_role is None:
            await self.send_error(
                ctx,
                error_code="E1022",
                command_name="induct",
                logging_message=str(GuestRoleDoesNotExist())
            )
            return

        if guest_role in induction_member.roles:
            await ctx.respond(
                ":information_source: No changes made. User has already been inducted. :information_source:",
                ephemeral=True
            )
            return

        if induction_member.bot:
            await self.send_error(
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

        try:
            interaction_reminder_opt_out_member: Interaction_Reminder_Opt_Out_Member = await Interaction_Reminder_Opt_Out_Member.objects.aget(
                hashed_member_id=Interaction_Reminder_Opt_Out_Member.hash_member_id(
                    interaction_member.id
                )
            )
        except Interaction_Reminder_Opt_Out_Member.DoesNotExist:
            pass
        else:
            await interaction_reminder_opt_out_member.adelete()

        await induction_member.add_roles(
            guest_role,  # type: ignore
            reason=f"{ctx.user} used TeX Bot slash-command: \"/induct\""
        )

        await ctx.respond("User inducted successfully.", ephemeral=True)

        async for message in induction_member.history():
            if "joined the CSS Discord server but have not yet introduced" in message.content:
                await message.delete(
                    reason="Delete interaction reminders after user is inducted."
                )


class Slash_Commands_Cog(Application_Commands_Cog):
    @staticmethod
    async def write_roles_autocomplete_get_channels(ctx: discord.AutocompleteContext):
        if ctx.interaction.user is None:
            return set()

        try:
            guild: Guild = ctx.bot.css_guild  # type: ignore
        except GuildDoesNotExist:
            return set()

        channel_permissions_limiter: Member | Role | None = discord.utils.get(guild.roles, name="@everyone")
        if channel_permissions_limiter is None:
            return set()

        interaction_member: Member | None = guild.get_member(ctx.interaction.user.id)
        if interaction_member:
            channel_permissions_limiter = interaction_member

        return {OptionChoice(name=f"#{channel.name}", value=str(channel.id)) for channel in guild.text_channels if channel.permissions_for(channel_permissions_limiter).is_superset(Permissions(send_messages=True, view_channel=True))}

    @staticmethod
    async def induct_autocomplete_get_members(ctx: discord.AutocompleteContext):
        try:
            guild: Guild = ctx.bot.css_guild  # type: ignore
        except GuildDoesNotExist:
            return set()

        members: set[Member] = {member for member in guild.members if not member.bot}

        guest_role: Role | None = ctx.bot.guest_role  # type: ignore
        if guest_role:
            members = {member for member in members if guest_role not in member.roles}

        return {OptionChoice(name=f"@{member.name}", value=str(member.id)) for member in members}

    @discord.slash_command(description="Replies with Pong!")
    async def ping(self, ctx: ApplicationContext):
        async for message in ctx.user.history():
            await message.delete()
        await ctx.respond(
            random.choices(
                [
                    "Pong!",
                    "64 bytes from TeX: icmp_seq=1 ttl=63 time=0.01 ms"
                ],
                weights=settings["PING_COMMAND_EASTER_EGG_WEIGHTS"]
            )[0],
            ephemeral=True
        )

    @discord.slash_command(description="Displays information about the source code of this bot.")
    async def source(self, ctx: ApplicationContext):
        await ctx.respond(
            "TeX is an open-source project made specifically for the CSS Discord! You can see and contribute to the source code at https://github.com/CSSUoB/TeX-Bot-Py",
            ephemeral=True
        )

    @discord.slash_command(
        name="remindme",
        description="Responds with the given message after the specified time."
    )
    @discord.option(
        name="delay",
        input_type=str,
        description="The amount of time to wait before reminding you",
        required=True
    )
    @discord.option(
        name="message",
        input_type=str,
        description="The message you want to be reminded with.",
        required=False
    )
    async def remind_me(self, ctx: ApplicationContext, delay: str, message: str):
        parsed_time: tuple[time.struct_time, int] = parsedatetime.Calendar().parseDT(delay, tzinfo=timezone.get_current_timezone())

        if parsed_time[1] == 0:
            await self.send_error(
                ctx,
                command_name="remind_me",
                message=f"The value provided in the \"delay\" argument was not a time/date."
            )
            return

        if message:
            message = re.sub(r"<@[&#]?\d+>", "@...", message.strip())

        try:
            reminder: Discord_Reminder = await Discord_Reminder.objects.acreate(
                member_id=ctx.user.id,
                message=message or "",
                channel_id=ctx.channel_id,
                send_datetime=parsed_time[0]
            )
        except ValidationError as create_interaction_reminder_opt_out_member_error:
            if "__all__" not in create_interaction_reminder_opt_out_member_error.message_dict or all("already exists" not in error for error in create_interaction_reminder_opt_out_member_error.message_dict["__all__"]):
                await self.send_error(
                    ctx,
                    command_name="remind_me",
                    message="An unrecoverable error occurred."
                )
                logging.critical(create_interaction_reminder_opt_out_member_error)
                await self.bot.close()
                return
            else:
                await self.send_error(
                    ctx,
                    command_name="remind_me",
                    message="You already have a reminder with that message in this channel!"
                )
                return

        await ctx.respond("Reminder set!", ephemeral=True)

        await discord.utils.sleep_until(reminder.send_datetime)

        user_mention: str | None = None
        if ctx.guild:
            user_mention = ctx.user.mention

        await ctx.send_followup(reminder.format_message(user_mention))

        await reminder.adelete()

    # noinspection SpellCheckingInspection
    @discord.slash_command(
        name="writeroles",
        description="Populates #roles with the correct messages."
    )
    async def write_roles(self, ctx: ApplicationContext):
        try:
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="write_roles"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        interaction_member: Member | None = guild.get_member(ctx.user.id)
        if interaction_member is None:
            await self.send_error(
                ctx,
                command_name="write_roles",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        committee_role: Role | None = self.bot.committee_role
        if committee_role is None:
            await self.send_error(
                ctx,
                error_code="E1021",
                command_name="write_roles",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        if committee_role not in interaction_member.roles:
            await self.send_error(
                ctx,
                command_name="write_roles",
                message=f"Only {committee_role.mention} members can run this command."
            )
            return

        roles_channel: TextChannel | None = self.bot.roles_channel
        if roles_channel is None:
            await self.send_error(
                ctx,
                error_code="E1031",
                command_name="write_roles",
                logging_message=str(RolesChannelDoesNotExist())
            )
            return

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
        autocomplete=discord.utils.basic_autocomplete(write_roles_autocomplete_get_channels),  # type: ignore
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
            await self.send_error(
                ctx,
                command_name="edit_message",
                message=f"\"{str_channel_id}\" is not a valid channel ID."
            )
            return

        channel_id: int = int(str_channel_id)

        if not re.match(r"\A\d{17,20}\Z", str_message_id):
            await self.send_error(
                ctx,
                command_name="edit_message",
                message=f"\"{str_message_id}\" is not a valid message ID."
            )
            return

        message_id: int = int(str_message_id)

        try:
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="edit_message"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        channel: TextChannel | None = discord.utils.get(guild.text_channels, id=channel_id)
        if channel is None:
            await self.send_error(
                ctx,
                command_name="edit_message",
                message=f"Text channel with ID \"{channel_id}\" does not exist."
            )
            return

        interaction_member: Member | None = guild.get_member(ctx.user.id)
        if interaction_member is None:
            await self.send_error(
                ctx,
                command_name="edit_message",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        committee_role: Role | None = self.bot.committee_role
        if committee_role is None:
            await self.send_error(
                ctx,
                error_code="E1021",
                command_name="edit_message",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        if committee_role not in interaction_member.roles:
            await self.send_error(
                ctx,
                command_name="edit_message",
                message=f"Only {committee_role.mention} members can run this command."
            )
            return

        try:
            message: Message = await channel.fetch_message(message_id)
        except NotFound:
            await self.send_error(
                ctx,
                command_name="edit_message",
                message=f"Message with ID \"{message_id}\" does not exist."
            )
            return

        try:
            await message.edit(content=new_message_content)
        except Forbidden:
            await self.send_error(
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
        autocomplete=discord.utils.basic_autocomplete(induct_autocomplete_get_members),  # type: ignore
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
    async def induct(self, ctx: ApplicationContext, str_induct_member_id: str, silent: bool):
        if not re.match(r"\A\d{17,20}\Z", str_induct_member_id):
            await self.send_error(
                ctx,
                command_name="induct",
                message=f"\"{str_induct_member_id}\" is not a valid user ID."
            )
            return

        induct_member_id: int = int(str_induct_member_id)

        try:
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="induct"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        induct_member: Member | None = guild.get_member(induct_member_id)
        if induct_member is None:
            await self.send_error(
                ctx,
                command_name="induct",
                message=f"Member with ID \"{induct_member_id}\" does not exist."
            )
            return

        await self._induct(ctx, induct_member, guild, silent)

    # noinspection SpellCheckingInspection
    @discord.slash_command(
        name="makemember",
        description="Gives you the Member role when supplied with an appropriate Student ID."
    )
    @discord.option(
        name="studentid",
        description="Your UoB Student ID",
        input_type=str,
        required=True,
        max_length=7,
        min_length=7,
        parameter_name="uob_id"
    )
    async def make_member(self, ctx: ApplicationContext, uob_id: str):
        if not re.match(r"\A\d{7}\Z", uob_id):
            await self.send_error(
                ctx,
                command_name="make_member",
                message=f"\"{uob_id}\" is not a valid UoB Student ID."
            )
            return

        try:
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="make_member"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        interaction_member: Member | None = guild.get_member(ctx.user.id)
        if interaction_member is None:
            await self.send_error(
                ctx,
                command_name="make_member",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        guest_role: Role | None = self.bot.guest_role
        if guest_role is None:
            await self.send_error(
                ctx,
                error_code="E1022",
                command_name="make_member",
                logging_message=str(GuestRoleDoesNotExist())
            )
            return

        if guest_role not in interaction_member.roles:
            await self.send_error(
                ctx,
                command_name="make_member",
                message="You must be a inducted as guest member of the CSS Discord server to use \"/makemember\"."
            )
            return

        member_role: Role | None = self.bot.member_role
        if member_role is None:
            await self.send_error(
                ctx,
                error_code="E1023",
                command_name="make_member",
                logging_message=str(MemberRoleDoesNotExist())
            )
            return

        if member_role in interaction_member.roles:
            await ctx.respond(
                ":information_source: No changes made. You're already a member - why are you trying this again? :information_source:",
                ephemeral=True
            )
            return

        if await UoB_Made_Member.objects.filter(hashed_uob_id=UoB_Made_Member.hash_uob_id(uob_id)).aexists():
            await ctx.respond(
                ":information_source: No changes made. This student ID has already been used. Please contact a Committee member if this is an error. :information_source:",
                ephemeral=True
            )
            return

        guild_member_ids: set[str] = set()

        async with aiohttp.ClientSession(headers={"Cache-Control": "no-cache", "Pragma": "no-cache", "Expires": "0"}, cookies={".ASPXAUTH": settings["MEMBERS_PAGE_COOKIE"]}) as http_session:
            async with http_session.get(url=settings["MEMBERS_PAGE_URL"]) as http_response:
                http_response_html: str = await http_response.text()

        guild_member_ids.update(row.contents[2].text for row in BeautifulSoup(http_response_html, "html.parser").find("table", {"id": "ctl00_Main_rptGroups_ctl05_gvMemberships"}).find_all("tr", {"class": ["msl_row", "msl_altrow"]}))  # type: ignore
        guild_member_ids.discard("")
        guild_member_ids.discard("\n")
        guild_member_ids.discard(" ")

        if not guild_member_ids:
            try:
                raise IOError("The guild member IDs could not be retrieved from the MEMBERS_PAGE_URL.")
            except IOError as guild_member_ids_error:
                await self.send_error(
                    ctx,
                    error_code="E1041",
                    command_name="make_member"
                )
                logging.critical(guild_member_ids_error)
                await self.bot.close()
                return

        if uob_id in guild_member_ids:
            await ctx.respond(
                "Successfully made you a member!",
                ephemeral=True
            )

            await interaction_member.add_roles(
                member_role,  # type: ignore
                reason=f"TeX Bot slash-command: \"/makemember\""
            )

            try:
                await UoB_Made_Member.objects.acreate(uob_id=uob_id)
            except ValidationError as create_uob_made_member_error:
                if "hashed_uob_id" not in create_uob_made_member_error.message_dict or all("already exists" not in error for error in create_uob_made_member_error.message_dict["hashed_uob_id"]):
                    raise

        else:
            await self.send_error(
                ctx,
                command_name="make_member",
                message="You must be a member of The Computer Science Society to use this command.\nThe provided student ID must match the UoB student ID that you purchased your CSS membership with."
            )
            return


class User_Commands_Cog(Application_Commands_Cog):
    async def _user_command_induct(self, ctx: ApplicationContext, member: Member, silent: bool):
        try:
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="induct"
            )
            logging.critical(guild_error)
            await self.bot.close()
            raise

        await self._induct(ctx, member, guild, silent)

    @discord.user_command(name="Induct User")
    async def non_silent_induct(self, ctx: ApplicationContext, member: Member):
        await self._user_command_induct(ctx, member, silent=False)

    @discord.user_command(name="Silently Induct User")
    async def silent_induct(self, ctx: ApplicationContext, member: Member):
        await self._user_command_induct(ctx, member, silent=True)


def setup(bot: TeXBot):
    bot.add_cog(Slash_Commands_Cog(bot))
    bot.add_cog(User_Commands_Cog(bot))
