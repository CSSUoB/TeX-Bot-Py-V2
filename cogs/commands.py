import logging
import math
import random
import re
import time

import aiohttp
import discord
import parsedatetime  # type: ignore
import bs4
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.utils import timezone

import utils
from cogs.utils import Bot_Cog
from db.core.models import DiscordReminder, LeftMember, UoBMadeMember
from exceptions import ArchivistRoleDoesNotExist, CommitteeRoleDoesNotExist, GeneralChannelDoesNotExist, GuestRoleDoesNotExist, GuildDoesNotExist, MemberRoleDoesNotExist, RolesChannelDoesNotExist
from config import Settings
from utils import TeXBot


class Application_Commands_Cog(Bot_Cog):
    ERROR_ACTIVITIES: dict[str, str] = {
        "ping": "reply with Pong!!",
        "write_roles": "send messages",
        "edit_message": "edit the message",
        "induct": "induct user",
        "make_member": "make you a member",
        "remind_me": "remind you",
        "channel_stats": "display channel statistics",
        "server_stats": "display whole server statistics",
        "user_stats": "display your statistics",
        "left_member_stats": "display statistics about the members that have left the server",
        "archive": "archive the selected category"
    }

    async def send_error(self, ctx: discord.ApplicationContext, error_code: str | None = None, command_name: str | None = None, message: str | None = None, logging_message: str | None = None):
        construct_error_message: str = ":warning:There was an error"
        construct_logging_error_message: str = ""

        if error_code:
            committee_mention: str = "committee"

            committee_role: discord.Role | None = self.bot.committee_role
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
            message = re.sub(r"<[@&#]?\d+>", lambda match: f"`{match.group(0)}`", message.strip())
            construct_error_message += f"\n`{message}`"

        await ctx.respond(construct_error_message, ephemeral=True)

        if logging_message:
            logging.error(f"{construct_logging_error_message} {logging_message}")

    async def _induct(self, ctx: discord.ApplicationContext, induction_member: discord.Member, guild: discord.Guild, silent: bool):
        guest_role: discord.Role | None = self.bot.guest_role
        if not guest_role:
            await self.send_error(
                ctx,
                error_code="E1022",
                command_name="induct",
                logging_message=str(GuestRoleDoesNotExist())
            )
            return

        committee_role: discord.Role | None = self.bot.committee_role
        if not committee_role:
            await self.send_error(
                ctx,
                error_code="E1021",
                command_name="induct",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                command_name="induct",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        if committee_role not in interaction_member.roles:
            committee_role_mention: str = "@Committee"
            if ctx.guild:
                committee_role_mention = committee_role.mention

            await self.send_error(
                ctx,
                command_name="induct",
                message=f"Only {committee_role_mention} members can run this command."
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
            general_channel: discord.TextChannel | None = self.bot.general_channel
            if not general_channel:
                await self.send_error(
                    ctx,
                    error_code="E1032",
                    command_name="induct",
                    logging_message=str(GeneralChannelDoesNotExist())
                )
                return

            roles_channel_mention: str = "`#roles`"

            roles_channel: discord.TextChannel | None = self.bot.roles_channel
            if roles_channel:
                roles_channel_mention = roles_channel.mention

            await general_channel.send(
                f"""{random.choice(Settings["WELCOME_MESSAGES"]).replace("<User>", induction_member.mention).strip()} :tada:\nRemember to grab your roles in {roles_channel_mention} and say hello to everyone here! :wave:"""
            )

        await induction_member.add_roles(
            guest_role,  # type: ignore
            reason=f"{ctx.user} used TeX Bot slash-command: \"/induct\""
        )

        await ctx.respond("User inducted successfully.", ephemeral=True)


class Slash_Commands_Cog(Application_Commands_Cog):
    stats: discord.SlashCommandGroup = discord.SlashCommandGroup("stats", "Various statistics about the CSS Discord server")

    @staticmethod
    async def remind_me_autocomplete_get_delays(ctx: discord.AutocompleteContext) -> set[str]:
        if not ctx.value:
            return {"in 5 minutes", "1 hours time", "1min", "30 secs", "2 days time", "22/9/2040", "5h"}

        seconds_choices: set[str] = {"s", "sec", "seconds"}
        minutes_choices: set[str] = {"m", "min", "mins"}
        hours_choices: set[str] = {"h", "hr", "hour"}
        days_choices: set[str] = {"d", "day"}
        weeks_choices: set[str] = {"w", "wk", "week"}
        years_choices: set[str] = {"y", "yr", "year"}
        time_choices: set[str] = seconds_choices | minutes_choices | hours_choices | days_choices | weeks_choices | years_choices

        delay_choices: set[str] = set()

        if re.match(r"\Ain? ?\Z", ctx.value):
            time_num: int
            for time_num in range(1, 150):
                joiner: str
                for joiner in {"", " "}:
                    has_s: str
                    for has_s in {"", "s"}:
                        delay_choices.update(f"{time_num}{joiner}{time_choice}{has_s}" for time_choice in time_choices)
                        delay_choices.update(f"{time_num}{joiner}{time_choice.title()}{has_s}" for time_choice in time_choices)
                        delay_choices.update(f"{time_num}{joiner}{time_choice.upper()}{has_s}" for time_choice in time_choices)

            return {f"in {delay_choice}" for delay_choice in delay_choices}

        if match := re.match(r"\Ain (?P<partial_date>\d{0,3})\Z", ctx.value):
            for joiner in {"", " "}:
                for has_s in {"", "s"}:
                    delay_choices.update(f"""{match.group("partial_date")}{joiner}{time_choice}{has_s}""" for time_choice in time_choices)
                    delay_choices.update(f"""{match.group("partial_date")}{joiner}{time_choice.title()}{has_s}""" for time_choice in time_choices)
                    delay_choices.update(f"""{match.group("partial_date")}{joiner}{time_choice.upper()}{has_s}""" for time_choice in time_choices)

            return {f"in {delay_choice}" for delay_choice in delay_choices}

        current_year: int = discord.utils.utcnow().year

        if re.match(r"\A\d{1,3}\Z", ctx.value):
            for joiner in {"", " "}:
                for has_s in {"", "s"}:
                    delay_choices.update(f"{joiner}{time_choice}{has_s}" for time_choice in time_choices)
                    delay_choices.update(f"{joiner}{time_choice.title()}{has_s}" for time_choice in time_choices)
                    delay_choices.update(f"{joiner}{time_choice.upper()}{has_s}" for time_choice in time_choices)

            if 1 <= int(ctx.value) <= 31:
                month: int
                for month in range(1, 12):
                    year: int
                    for year in range(current_year, current_year + 40):
                        for joiner in {"/", " / ", "-", " - ", ".", " . "}:
                            delay_choices.add(f"{joiner}{month}{joiner}{year}")
                            if month < 10:
                                delay_choices.add(f"{joiner}0{month}{joiner}{year}")

        elif match := re.match(r"\A(?P<date>\d{1,2}) ?[/\-.] ?\Z", ctx.value):
            if 1 <= int(match.group("date")) <= 31:
                for month in range(1, 12):
                    for year in range(current_year, current_year + 40):
                        for joiner in {"/", " / ", "-", " - ", ".", " . "}:
                            delay_choices.add(f"{month}{joiner}{year}")
                            if month < 10:
                                delay_choices.add(f"0{month}{joiner}{year}")

        elif match := re.match(r"\A(?P<date>\d{1,2}) ?[/\-.] ?(?P<month>\d{1,2})\Z", ctx.value):
            if 1 <= int(match.group("date")) <= 31 and 1 <= int(match.group("month")) <= 12:
                for year in range(current_year, current_year + 40):
                    for joiner in {"/", " / ", "-", " - ", ".", " . "}:
                        delay_choices.add(f"{joiner}{year}")

        elif match := re.match(r"\A(?P<date>\d{1,2}) ?[/\-.] ?(?P<month>\d{1,2}) ?[/\-.] ?\Z", ctx.value):
            if 1 <= int(match.group("date")) <= 31 and 1 <= int(match.group("month")) <= 12:
                for year in range(current_year, current_year + 40):
                    delay_choices.add(f"{year}")

        elif match := re.match(r"\A(?P<date>\d{1,2}) ?[/\-.] ?(?P<month>\d{1,2}) ?[/\-.] ?(?P<partial_year>\d{1,3})\Z", ctx.value):
            if 1 <= int(match.group("date")) <= 31 and 1 <= int(match.group("month")) <= 12:
                for year in range(current_year, current_year + 40):
                    delay_choices.add(f"{year}"[len(match.group("partial_year")):])

        return {f"{ctx.value}{delay_choice}" for delay_choice in delay_choices}

    @staticmethod
    async def autocomplete_get_text_channels(ctx: discord.AutocompleteContext) -> set[discord.OptionChoice]:
        if not ctx.interaction.user:
            return set()

        try:
            guild: discord.Guild = ctx.bot.css_guild  # type: ignore
        except GuildDoesNotExist:
            return set()

        channel_permissions_limiter: discord.Member | discord.Role | None = ctx.bot.guest_role  # type: ignore
        if not channel_permissions_limiter:
            return set()

        interaction_member: discord.Member | None = guild.get_member(ctx.interaction.user.id)
        if interaction_member:
            channel_permissions_limiter = interaction_member

        if not ctx.value or re.match(r"\A#.*\Z", ctx.value):
            return {discord.OptionChoice(name=f"#{channel.name}", value=str(channel.id)) for channel in guild.text_channels if channel.permissions_for(channel_permissions_limiter).is_superset(discord.Permissions(send_messages=True, view_channel=True))}

        else:
            return {discord.OptionChoice(name=channel.name, value=str(channel.id)) for channel in guild.text_channels if channel.permissions_for(channel_permissions_limiter).is_superset(discord.Permissions(send_messages=True, view_channel=True))}

    @staticmethod
    async def archive_autocomplete_get_categories(ctx: discord.AutocompleteContext) -> set[discord.OptionChoice]:
        if not ctx.interaction.user:
            return set()

        try:
            guild: discord.Guild = ctx.bot.css_guild  # type: ignore
        except GuildDoesNotExist:
            return set()

        committee_role: discord.Role | None = ctx.bot.committee_role  # type: ignore
        if not committee_role:
            return set()

        interaction_member: discord.Member | None = guild.get_member(ctx.interaction.user.id)
        if not interaction_member:
            return set()

        if committee_role not in interaction_member.roles:
            return set()

        return {discord.OptionChoice(name=category.name, value=str(category.id)) for category in guild.categories if category.permissions_for(interaction_member).is_superset(discord.Permissions(send_messages=True, view_channel=True))}

    @staticmethod
    async def induct_autocomplete_get_members(ctx: discord.AutocompleteContext) -> set[discord.OptionChoice]:
        try:
            guild: discord.Guild = ctx.bot.css_guild  # type: ignore
        except GuildDoesNotExist:
            return set()

        members: set[discord.Member] = {member for member in guild.members if not member.bot}

        guest_role: Role | None = ctx.bot.guest_role  # type: ignore
        if guest_role:
            members = {member for member in members if guest_role not in member.roles}

        if not ctx.value or re.match(r"\A@.*\Z", ctx.value):
            return {discord.OptionChoice(name=f"@{member.name}", value=str(member.id)) for member in members}

        else:
            return {discord.OptionChoice(name=member.name, value=str(member.id)) for member in members}

    @discord.slash_command(description="Replies with Pong!")
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            random.choices(
                [
                    "Pong!",
                    "64 bytes from TeX: icmp_seq=1 ttl=63 time=0.01 ms"
                ],
                weights=Settings["PING_COMMAND_EASTER_EGG_WEIGHTS"]
            )[0],
            ephemeral=True
        )

    @discord.slash_command(description="Displays information about the source code of this bot.")
    async def source(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            "TeX is an open-source project made specifically for the CSS Discord! You can see and contribute to the source code at https://github.com/CSSUoB/TeX-Bot-Py-V2",
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
        required=True,
        autocomplete=discord.utils.basic_autocomplete(remind_me_autocomplete_get_delays),  # type: ignore
    )
    @discord.option(
        name="message",
        input_type=str,
        description="The message you want to be reminded with.",
        required=False
    )
    async def remind_me(self, ctx: discord.ApplicationContext, delay: str, message: str):
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
            reminder: DiscordReminder = await DiscordReminder.objects.acreate(
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
    async def write_roles(self, ctx: discord.ApplicationContext):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="write_roles"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        committee_role: discord.Role | None = self.bot.committee_role
        if not committee_role:
            await self.send_error(
                ctx,
                error_code="E1021",
                command_name="write_roles",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        roles_channel: discord.TextChannel | None = self.bot.roles_channel
        if not roles_channel:
            await self.send_error(
                ctx,
                error_code="E1031",
                command_name="write_roles",
                logging_message=str(RolesChannelDoesNotExist())
            )
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                command_name="write_roles",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        if committee_role not in interaction_member.roles:
            committee_role_mention: str = "@Committee"
            if ctx.guild:
                committee_role_mention = committee_role.mention

            await self.send_error(
                ctx,
                command_name="write_roles",
                message=f"Only {committee_role_mention} members can run this command."
            )
            return

        roles_message: str
        for roles_message in Settings["ROLES_MESSAGES"]:
            await roles_channel.send(roles_message)

        await ctx.respond("All messages sent successfully.", ephemeral=True)

    # noinspection SpellCheckingInspection
    @discord.slash_command(
        name="editmessage",
        description="Edits a message sent by TeX-Bot to the value supplied."
    )
    @discord.option(
        name="channel",
        description="The channel that the message, you wish to edit, is in.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_text_channels),  # type: ignore
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
    async def edit_message(self, ctx: discord.ApplicationContext, str_channel_id: str, str_message_id: str, new_message_content: str):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="edit_message"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        committee_role: discord.Role | None = self.bot.committee_role
        if not committee_role:
            await self.send_error(
                ctx,
                error_code="E1021",
                command_name="edit_message",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                command_name="edit_message",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        if committee_role not in interaction_member.roles:
            committee_role_mention: str = "@Committee"
            if ctx.guild:
                committee_role_mention = committee_role.mention

            await self.send_error(
                ctx,
                command_name="edit_message",
                message=f"Only {committee_role_mention} members can run this command."
            )
            return

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

        channel: discord.TextChannel | None = discord.utils.get(guild.text_channels, id=channel_id)
        if not channel:
            await self.send_error(
                ctx,
                command_name="edit_message",
                message=f"Text channel with ID \"{channel_id}\" does not exist."
            )
            return

        try:
            message: discord.Message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await self.send_error(
                ctx,
                command_name="edit_message",
                message=f"Message with ID \"{message_id}\" does not exist."
            )
            return

        try:
            await message.edit(content=new_message_content)
        except discord.Forbidden:
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
    async def induct(self, ctx: discord.ApplicationContext, str_induct_member_id: str, silent: bool):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="induct"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        if not re.match(r"\A\d{17,20}\Z", str_induct_member_id):
            await self.send_error(
                ctx,
                command_name="induct",
                message=f"\"{str_induct_member_id}\" is not a valid user ID."
            )
            return

        induct_member_id: int = int(str_induct_member_id)

        induct_member: discord.Member | None = guild.get_member(induct_member_id)
        if not induct_member:
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
    async def make_member(self, ctx: discord.ApplicationContext, uob_id: str):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="make_member"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        member_role: discord.Role | None = self.bot.member_role
        if not member_role:
            await self.send_error(
                ctx,
                error_code="E1023",
                command_name="make_member",
                logging_message=str(MemberRoleDoesNotExist())
            )
            return

        guest_role: discord.Role | None = self.bot.guest_role
        if not guest_role:
            await self.send_error(
                ctx,
                error_code="E1022",
                command_name="make_member",
                logging_message=str(GuestRoleDoesNotExist())
            )
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                command_name="make_member",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        if member_role in interaction_member.roles:
            await ctx.respond(
                ":information_source: No changes made. You're already a member - why are you trying this again? :information_source:",
                ephemeral=True
            )
            return

        if guest_role not in interaction_member.roles:
            await self.send_error(
                ctx,
                command_name="make_member",
                message="You must be a inducted as guest member of the CSS Discord server to use \"/makemember\"."
            )
            return

        if not re.match(r"\A\d{7}\Z", uob_id):
            await self.send_error(
                ctx,
                command_name="make_member",
                message=f"\"{uob_id}\" is not a valid UoB Student ID."
            )
            return

        if await UoBMadeMember.objects.filter(hashed_uob_id=UoBMadeMember.hash_uob_id(uob_id)).aexists():
            committee_mention: str = "committee"

            committee_role: discord.Role | None = self.bot.committee_role
            if committee_role:
                committee_mention = committee_role.mention

            await ctx.respond(
                f":information_source: No changes made. This student ID has already been used. Please contact a {committee_mention} member if this is an error. :information_source:",
                ephemeral=True
            )
            return

        guild_member_ids: set[str] = set()

        async with aiohttp.ClientSession(headers={"Cache-Control": "no-cache", "Pragma": "no-cache", "Expires": "0"}, cookies={".ASPXAUTH": Settings["MEMBERS_PAGE_COOKIE"]}) as http_session:
            async with http_session.get(url=Settings["MEMBERS_PAGE_URL"]) as http_response:
                response_html: str = await http_response.text()

        filtered_response_html: bs4.Tag | None = BeautifulSoup(response_html, "html.parser").find("table", {"id": "ctl00_Main_rptGroups_ctl05_gvMemberships"})

        if filtered_response_html:
            guild_member_ids.update(row.contents[2].text for row in filtered_response_html.find_all("tr", {"class": ["msl_row", "msl_altrow"]}))
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
                await UoBMadeMember.objects.acreate(uob_id=uob_id)
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

    # noinspection SpellCheckingInspection
    @stats.command(
        name="channel",
        description="Displays the stats for the current/a given channel."
    )
    @discord.option(
        name="channel",
        description="The channel to display the stats for.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_text_channels),  # type: ignore
        required=False,
        parameter_name="str_channel_id"
    )
    async def channel_stats(self, ctx: discord.ApplicationContext, str_channel_id: str):
        channel_id: int = ctx.channel_id

        if str_channel_id:
            if not re.match(r"\A\d{17,20}\Z", str_channel_id):
                await self.send_error(
                    ctx,
                    command_name="channel_stats",
                    message=f"\"{str_channel_id}\" is not a valid channel ID."
                )
                return

            channel_id = int(str_channel_id)

        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="channel_stats"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        channel: discord.TextChannel | None = discord.utils.get(guild.text_channels, id=channel_id)
        if not channel:
            await self.send_error(
                ctx,
                command_name="channel_stats",
                message=f"Text channel with ID \"{channel_id}\" does not exist."
            )
            return

        message_counts: dict[str, int] = {"Total": 0}

        role_name: str
        for role_name in Settings["STATISTICS_ROLES"]:
            if discord.utils.get(guild.roles, name=role_name):
                message_counts[f"@{role_name}"] = 0

        message: discord.Message
        async for message in channel.history(after=discord.utils.utcnow() - Settings["STATISTICS_DAYS"]):
            if message.author.bot:
                continue

            message_counts["Total"] += 1

            if isinstance(message.author, discord.User):
                continue

            author_role_names: set[str] = {author_role.name for author_role in message.author.roles}

            author_role_name: str
            for author_role_name in author_role_names:
                if f"@{author_role_name}" in message_counts.keys():
                    if author_role_name == "Committee" and "Committee-Elect" in author_role_names:
                        continue

                    if author_role_name == "Guest" and "Member" in author_role_names:
                        continue

                    message_counts[f"@{author_role_name}"] += 1

        if math.ceil(max(message_counts.values()) / 15) < 1:
            await self.send_error(
                ctx,
                command_name="channel_stats",
                message=f"There are not enough messages sent in this channel."
            )
            return

        await ctx.respond(
            file=utils.plot_bar_chart(
                message_counts,
                xlabel="Role Name",
                ylabel=f"""Number of Messages Sent (in the past {utils.amount_of_time_formatter(Settings["STATISTICS_DAYS"].days, "day")})""",
                title=f"Most Active Roles in #{channel.name}",
                filename=f"{channel.name}_channel_stats.png",
                description=f"Bar chart of the number of messages sent by different roles in {channel.mention}.",
                extra_text="Messages sent by members with multiple roles are counted once for each role (except for @Member vs @Guest & @Committee vs @Committee-Elect)"
            )
        )

    @stats.command(
        name="server",
        description="Displays the stats for the whole of the CSS Discord server."
    )
    async def server_stats(self, ctx: discord.ApplicationContext):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="server_stats"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        guest_role: discord.Role | None = self.bot.guest_role
        if not guest_role:
            await self.send_error(
                ctx,
                error_code="E1022",
                command_name="server_stats",
                logging_message=str(GuestRoleDoesNotExist())
            )
            return

        message_counts: dict[str, dict[str, int]] = {
            "roles": {"Total": 0},
            "channels": {}
        }

        role_name: str
        for role_name in Settings["STATISTICS_ROLES"]:
            if discord.utils.get(guild.roles, name=role_name):
                message_counts["roles"][f"@{role_name}"] = 0

        channel: discord.TextChannel
        for channel in guild.text_channels:
            if not channel.permissions_for(guest_role).is_superset(discord.Permissions(send_messages=True)):
                continue

            message_counts["channels"][f"#{channel.name}"] = 0

            message: discord.Message
            async for message in channel.history(after=discord.utils.utcnow() - Settings["STATISTICS_DAYS"]):
                if message.author.bot:
                    continue

                message_counts["channels"][f"#{channel.name}"] += 1
                message_counts["roles"]["Total"] += 1

                if isinstance(message.author, discord.User):
                    continue

                author_role_names: set[str] = {author_role.name for author_role in message.author.roles}

                author_role_name: str
                for author_role_name in author_role_names:
                    if f"@{author_role_name}" in message_counts["roles"].keys():
                        if author_role_name == "Committee" and "Committee-Elect" in author_role_names:
                            continue

                        if author_role_name == "Guest" and "Member" in author_role_names:
                            continue

                        message_counts["roles"][f"@{author_role_name}"] += 1

        if math.ceil(max(message_counts["roles"].values()) / 15) < 1 or math.ceil(max(message_counts["channels"].values()) / 15) < 1:
            await self.send_error(
                ctx,
                command_name="server_stats",
                message="There are not enough messages sent."
            )
            return

        await ctx.respond(
            files=[
                utils.plot_bar_chart(
                    message_counts["roles"],
                    xlabel="Role Name",
                    ylabel=f"""Number of Messages Sent (in the past {utils.amount_of_time_formatter(Settings["STATISTICS_DAYS"].days, "day")})""",
                    title="Most Active Roles in the CSS Discord Server",
                    filename="roles_server_stats.png",
                    description="Bar chart of the number of messages sent by different roles in the CSS Discord server.",
                    extra_text="Messages sent by members with multiple roles are counted once for each role (except for @Member vs @Guest & @Committee vs @Committee-Elect)"
                ),
                utils.plot_bar_chart(
                    message_counts["channels"],
                    xlabel="Channel Name",
                    ylabel=f"""Number of Messages Sent (in the past {utils.amount_of_time_formatter(Settings["STATISTICS_DAYS"].days, "day")})""",
                    title="Most Active Channels in the CSS Discord Server",
                    filename="channels_server_stats.png",
                    description="Bar chart of the number of messages sent in different text channels in the CSS Discord server."
                ),
            ]
        )

    @stats.command(
        name="self",
        description="Displays stats about the number of messages you have sent."
    )
    async def user_stats(self, ctx: discord.ApplicationContext):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="user_stats"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                command_name="user_stats",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        guest_role: discord.Role | None = self.bot.guest_role
        if not guest_role:
            await self.send_error(
                ctx,
                error_code="E1022",
                command_name="user_stats",
                logging_message=str(GuestRoleDoesNotExist())
            )
            return

        if guest_role not in interaction_member.roles:
            await self.send_error(
                ctx,
                command_name="user_stats",
                message="You must be a inducted as guest member of the CSS Discord server to use this command."
            )
            return

        message_counts: dict[str, int] = {"Total": 0}

        channel: discord.TextChannel
        for channel in guild.text_channels:
            if not channel.permissions_for(guest_role).is_superset(discord.Permissions(send_messages=True)):
                continue

            message_counts[f"#{channel.name}"] = 0

            message: discord.Message
            async for message in channel.history(after=discord.utils.utcnow() - Settings["STATISTICS_DAYS"]):
                if message.author == ctx.user and not message.author.bot:
                    message_counts[f"#{channel.name}"] += 1
                    message_counts["Total"] += 1

        if math.ceil(max(message_counts.values()) / 15) < 1:
            await self.send_error(
                ctx,
                command_name="user_stats",
                message=f"You have not sent enough messages."
            )
            return

        await ctx.respond(
            file=utils.plot_bar_chart(
                message_counts,
                xlabel="Channel Name",
                ylabel=f"""Number of Messages Sent (in the past {utils.amount_of_time_formatter(Settings["STATISTICS_DAYS"].days, "day")})""",
                title="Your Most Active Channels in the CSS Discord Server",
                filename=f"{ctx.user}_stats.png",
                description=f"Bar chart of the number of messages sent by {ctx.user} in different channels in the CSS Discord server."
            )
        )

    # noinspection SpellCheckingInspection
    @stats.command(
        name="leftmembers",
        description="Displays the stats about members that have left the CSS Discord server."
    )
    async def left_member_stats(self, ctx: discord.ApplicationContext):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="left_member_stats"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        left_member_counts: dict[str, int] = {
            "Total": await LeftMember.objects.acount()
        }

        role_name: str
        for role_name in Settings["STATISTICS_ROLES"]:
            if discord.utils.get(guild.roles, name=role_name):
                left_member_counts[f"@{role_name}"] = 0

        left_member: LeftMember
        async for left_member in LeftMember.objects.all():
            for left_member_role in left_member.roles:
                if left_member_role not in left_member_counts:
                    continue

                if left_member_role == "@Committee" and "@Committee-Elect" in left_member.roles:
                    continue

                if left_member_role == "@Guest" and "@Member" in left_member.roles:
                    continue

                left_member_counts[left_member_role] += 1

        if math.ceil(max(left_member_counts.values()) / 15) < 1:
            await self.send_error(
                ctx,
                command_name="left_member_stats",
                message=f"Not enough data about members that have left the server."
            )
            return

        await ctx.respond(
            file=utils.plot_bar_chart(
                left_member_counts,
                xlabel="Role Name",
                ylabel="Number of Members that have left the CSS Discord Server",
                title="Most Common Roles that Members had when they left the CSS Discord Server",
                filename="left_members_stats.png",
                description="Bar chart of the number of members with different roles that have left the CSS Discord server.",
                extra_text="Members that left with multiple roles are counted once for each role (except for @Member vs @Guest & @Committee vs @Committee-Elect)"
            )
        )

    @discord.slash_command(
        name="archive",
        description="Archives the selected category."
    )
    @discord.option(
        name="category",
        description="The category to archive.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(archive_autocomplete_get_categories),  # type: ignore
        required=True,
        parameter_name="str_category_id"
    )
    async def archive(self, ctx: discord.ApplicationContext, str_category_id: str):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="archive"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        interaction_member: discord.Member | None = guild.get_member(ctx.user.id)
        if not interaction_member:
            await self.send_error(
                ctx,
                command_name="archive",
                message="You must be a member of the CSS Discord server to use this command."
            )
            return

        committee_role: discord.Role | None = self.bot.committee_role
        if not committee_role:
            await self.send_error(
                ctx,
                error_code="E1021",
                command_name="archive",
                logging_message=str(CommitteeRoleDoesNotExist())
            )
            return

        guest_role: discord.Role | None = self.bot.guest_role
        if not guest_role:
            await self.send_error(
                ctx,
                error_code="E1022",
                command_name="archive",
                logging_message=str(GuestRoleDoesNotExist())
            )
            return

        archivist_role: discord.Role | None = self.bot.archivist_role
        if not archivist_role:
            await self.send_error(
                ctx,
                error_code="E1024",
                command_name="archive",
                logging_message=str(ArchivistRoleDoesNotExist())
            )
            return

        if committee_role not in interaction_member.roles:
            committee_role_mention: str = "@Committee"
            if ctx.guild:
                committee_role_mention = f"`{committee_role.mention}`"

            await self.send_error(
                ctx,
                command_name="archive",
                message=f"Only {committee_role_mention} members can run this command."
            )
            return

        if not re.match(r"\A\d{17,20}\Z", str_category_id):
            await self.send_error(
                ctx,
                command_name="archive",
                message=f"\"{str_category_id}\" is not a valid category ID."
            )
            return

        category_id: int = int(str_category_id)

        category: discord.CategoryChannel | None = discord.utils.get(guild.categories, id=category_id)
        if not category:
            await self.send_error(
                ctx,
                command_name="archive",
                message=f"Category with ID \"{category_id}\" does not exist."
            )
            return

        if "archive" in category.name:
            await ctx.respond(
                ":information_source: No changes made. Category has already been archived. :information_source:",
                ephemeral=True
            )
            return

        await self.send_error(  # FIXME: Remove this warning after the way to correctly change permissions has been implemented
            ctx,
            command_name="archive",
            message=f"THIS COMMAND IS IN BETA (does not currently change permissions)"
        )
        return

        # noinspection PyUnreachableCode
        channel: discord.VoiceChannel | discord.StageChannel | discord.TextChannel | discord.ForumChannel | discord.CategoryChannel
        for channel in category.channels:
            try:
                if channel.permissions_for(committee_role).is_superset(discord.Permissions(view_channel=True)) and not channel.permissions_for(guest_role).is_superset(discord.Permissions(view_channel=True)):
                    pass  # TODO: Confirm how to correctly change permissions to archive committee-only channel

                elif channel.permissions_for(guest_role).is_superset(discord.Permissions(view_channel=True)):
                    pass  # TODO: Confirm how to correctly change permissions to archive public channel

                else:
                    await self.send_error(
                        ctx,
                        command_name="archive",
                        message=f"Channel {channel.mention} had invalid permissions"
                    )
                    return

                # await category.edit(name=f"Archived - {category.name}")

            except discord.Forbidden:
                await self.send_error(
                    ctx,
                    command_name="archive",
                    message=f"Bot does not have access to the channels in the selected category."
                )
                return

        await ctx.respond("Category successfully archived", ephemeral=True)


class User_Commands_Cog(Application_Commands_Cog):
    async def _user_command_induct(self, ctx: discord.ApplicationContext, member: discord.Member, silent: bool):
        try:
            guild: discord.Guild = self.bot.css_guild
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
    async def non_silent_induct(self, ctx: discord.ApplicationContext, member: discord.Member):
        await self._user_command_induct(ctx, member, silent=False)

    @discord.user_command(name="Silently Induct User")
    async def silent_induct(self, ctx: discord.ApplicationContext, member: discord.Member):
        await self._user_command_induct(ctx, member, silent=True)


def setup(bot: TeXBot):
    bot.add_cog(Slash_Commands_Cog(bot))
    bot.add_cog(User_Commands_Cog(bot))
