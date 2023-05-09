import hashlib
import json
import logging
import random
import re
from typing import Any

import aiofiles
import aiofiles.os
import aiohttp
import discord
from bs4 import BeautifulSoup
from discord import ApplicationContext, Forbidden, Guild, Member, Message, NotFound, OptionChoice, Permissions, Role, TextChannel

from .cog_utils import Bot_Cog
from exceptions import CommitteeRoleDoesNotExist, GeneralChannelDoesNotExist, GuestRoleDoesNotExist, GuildDoesNotExist, MemberRoleDoesNotExist, RolesChannelDoesNotExist
from setup import settings
from utils import TeXBot


class Application_Commands_Cog(Bot_Cog):
    ERROR_ACTIVITIES: dict[str, str] = {
        "ping": "reply with Pong!!",
        "write_roles": "send messages",
        "edit_message": "edit the message",
        "induct": "induct user",
        "make_member": "make you a member"
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
            message = re.sub(r"<@[&#]*\d{17,20}>", lambda match: f"`{match.group(0)}`", message.strip())
            construct_error_message += f"\n`{message}`"

        await ctx.respond(construct_error_message, ephemeral=True)

        if logging_message:
            logging.error(f"{construct_logging_error_message} {logging_message}")

    async def _induct(self, ctx: discord.ApplicationContext, induction_member: Member, guild: Guild, silent: bool):
        interaction_member: Member | None = await guild.fetch_member(ctx.user.id)
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

        await induction_member.add_roles(
            guest_role,  # type: ignore
            reason=f"{ctx.user} used TeX Bot slash-command: \"/induct\""
        )

        await ctx.respond("User inducted successfully.", ephemeral=True)


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

        interaction_member: Member | None = await guild.fetch_member(ctx.interaction.user.id)
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
        await ctx.respond(
            random.choices(
                [
                    "Pong!",
                    "64 bytes from TeX: icmp_seq=1 ttl=63 time=0.01 ms"
                ],
                weights=settings["PING_COMMAND_EASTER_EGG_WEIGHTS"]
            )[0]
        )
        logging.info(f"{ctx.user} made me pong!!")

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
            await self.send_error(
                ctx,
                error_code="E1011",
                command_name="write_roles"
            )
            logging.critical(guild_error)
            await self.bot.close()
            return

        interaction_member: Member | None = await guild.fetch_member(ctx.user.id)
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

        interaction_member: Member | None = await guild.fetch_member(ctx.user.id)
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

        induct_member: Member | None = await guild.fetch_member(induct_member_id)
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
        parameter_name="student_id"
    )
    async def make_member(self, ctx: ApplicationContext, student_id: str):
        if not re.match(r"\A\d{7}\Z", student_id):
            await self.send_error(
                ctx,
                command_name="make_member",
                message=f"\"{student_id}\" is not a valid UoB Student ID."
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

        interaction_member: Member | None = await guild.fetch_member(ctx.user.id)
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

        made_members: set[str] = set()

        if await aiofiles.os.path.isfile(settings["MADE_MEMBERS_FILE_PATH"]):
            async with aiofiles.open(settings["MADE_MEMBERS_FILE_PATH"], "r", encoding="utf8") as made_members_read_file:
                made_members_dict: dict = json.loads(
                    await made_members_read_file.read()
                )

            if "made_members" in made_members_dict:
                made_members_list: Any = made_members_dict["made_members"]

                if made_members_list and isinstance(made_members_list, list):
                    made_members = set(made_members_list)

        hashed_student_id: str = hashlib.sha256(student_id.encode()).hexdigest()

        if hashed_student_id in made_members:
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

        if student_id in guild_member_ids:
            await ctx.respond(
                "Successfully made you a member!",
                ephemeral=True
            )

            await interaction_member.add_roles(
                member_role,  # type: ignore
                reason=f"TeX Bot slash-command: \"/makemember\""
            )

            made_members.add(hashed_student_id)

            await aiofiles.os.makedirs(
                settings["MADE_MEMBERS_FILE_PATH"].parent,
                exist_ok=True
            )

            async with aiofiles.open(settings["MADE_MEMBERS_FILE_PATH"], "w", encoding="utf8") as made_members_write_file:
                await made_members_write_file.write(
                    json.dumps({"made_members": list(made_members)})
                )

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
