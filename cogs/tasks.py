import json
import logging
from datetime import timedelta
from typing import Any

import aiofiles
import aiofiles.os
import discord
import emoji
from discord import ActionRow, Button, Forbidden, Guild, Member, PartialEmoji, Role
from discord import ButtonStyle, Interaction, ui
from discord.ext import tasks
from discord.ui import View

from exceptions import GuestRoleDoesNotExist, GuildDoesNotExist
from setup import settings
from utils import TeXBot
from .cog_utils import Bot_Cog


class Tasks_Cog(Bot_Cog):
    def __init__(self, bot: TeXBot) -> None:
        if settings["SEND_INTRODUCTION_REMINDERS"]:
            self.introduction_reminder.start()

        if settings["KICK_NO_INTRODUCTION_MEMBERS"]:
            self.kick_no_introduction_members.start()

        super().__init__(bot)

    def cog_unload(self):
        self.introduction_reminder.cancel()
        self.kick_no_introduction_members.cancel()

    @tasks.loop(hours=24)
    async def kick_no_introduction_members(self):
        try:
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        guest_role: Role | None = self.bot.guest_role
        if guest_role is None:
            logging.critical(GuestRoleDoesNotExist())
            await self.bot.close()
            return

        member: Member
        for member in guild.members:
            if guest_role in member.roles or member.bot:
                continue

            if member.joined_at is None:
                logging.error(
                    f"Member with ID: {member.id} could not be checked whether to kick, because their \"joined_at\" attribute was None."
                )
                continue

            kick_no_introduction_members_delay: timedelta = timedelta(**settings["KICK_NO_INTRODUCTION_MEMBERS_DELAY"])

            if (discord.utils.utcnow() - member.joined_at) > kick_no_introduction_members_delay:
                try:
                    await member.kick(
                        reason=f"Member was in server without introduction sent for longer than {kick_no_introduction_members_delay}"
                    )
                except Forbidden as kick_error:
                    logging.warning(f"Member with ID: {member.id} could not be kicked due to {kick_error.text}")

    @kick_no_introduction_members.before_loop
    async def before_kick_no_introduction_members(self):
        await self.bot.wait_until_ready()

    @tasks.loop(**settings["INTRODUCTION_REMINDER_INTERVAL"])
    async def introduction_reminder(self):
        try:
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        guest_role: Role | None = self.bot.guest_role
        if guest_role is None:
            logging.critical(GuestRoleDoesNotExist())
            await self.bot.close()
            return

        opted_out_member_ids: set[str] = set()

        if await aiofiles.os.path.isfile(settings["MEMBERS_LISTS_FILE_PATH"]):
            async with aiofiles.open(settings["MEMBERS_LISTS_FILE_PATH"], "r", encoding="utf8") as members_lists_read_file:
                members_lists_dict: dict[str, Any] = json.loads(
                    await members_lists_read_file.read()
                )

            if "opted_out_members" in members_lists_dict:
                opted_out_members_list: Any = members_lists_dict["opted_out_members"]

                if opted_out_members_list and isinstance(opted_out_members_list, list):
                    opted_out_member_ids = set(opted_out_members_list)

        member: Member
        for member in guild.members:
            if guest_role in member.roles or member.bot:
                continue

            if str(member.id) not in opted_out_member_ids:
                async for message in member.history():
                    if message.components and isinstance(message.components[0], ActionRow) and isinstance(message.components[0].children[0], Button) and message.components[0].children[0].custom_id == "opt_out_introduction_reminders_button":
                        await message.edit(view=None)

                await member.send(
                    "Hey! It seems like you joined the CSS Discord server but have not yet introduced yourself.\nYou will only get access to the rest of the server after sending an introduction message.",
                    view=self.Opt_Out_Introduction_Reminders_View(self.bot)
                )

    @introduction_reminder.before_loop
    async def before_introduction_reminder(self):
        await self.bot.wait_until_ready()

    class Opt_Out_Introduction_Reminders_View(View):
        def __init__(self, bot: TeXBot):
            self.bot: TeXBot = bot

            super().__init__(timeout=None)

        @ui.button(
            label="Opt-out of introduction reminders", custom_id="opt_out_introduction_reminders_button",
            style=ButtonStyle.red, emoji=PartialEmoji.from_str(emoji.emojize(":no_good:", language="alias"))
        )
        async def opt_out_introduction_reminders_button_callback(self, button: Button, interaction: Interaction):
            try:
                guild: Guild = self.bot.css_guild
            except GuildDoesNotExist as guild_error:
                logging.critical(guild_error)
                await self.bot.close()
                return

            if interaction.user is None:
                await interaction.response.send_message(
                    ":warning:There was an error when trying to opt-in/out of interaction reminders.:warning:",
                    ephemeral=True
                )
                return

            opted_out_members: set[str] = set()
            members_lists_dict: dict[str, Any] = {}

            if await aiofiles.os.path.isfile(settings["MEMBERS_LISTS_FILE_PATH"]):
                async with aiofiles.open(
                        settings["MEMBERS_LISTS_FILE_PATH"], "r",
                        encoding="utf8"
                ) as members_lists_read_file:
                    members_lists_dict = json.loads(
                        await members_lists_read_file.read()
                    )

                if "opted_out_members" in members_lists_dict:
                    opted_out_members_list: Any = members_lists_dict["opted_out_members"]

                    if opted_out_members_list and isinstance(opted_out_members_list, list):
                        opted_out_members = set(opted_out_members_list)

            interaction_member: Member | None = guild.get_member(interaction.user.id)
            if button.style == ButtonStyle.red or str(button.emoji) == emoji.emojize(":no_good:", language="alias"):
                if interaction_member is None:
                    await interaction.response.send_message(
                        ":warning:There was an error when trying to opt-out of interaction reminders.:warning:\n`You must be a member of the CSS Discord server to opt-out of interaction reminders.`",
                        ephemeral=True
                    )
                    return

                button.style = ButtonStyle.green
                button.label = "Opt back in to introduction reminders"
                button.emoji = PartialEmoji.from_str(emoji.emojize(":raised_hand:", language="alias"))

                opted_out_members.add(str(interaction_member.id))

                members_lists_dict["opted_out_members"] = list(opted_out_members)

                await aiofiles.os.makedirs(
                    settings["MEMBERS_LISTS_FILE_PATH"].parent,
                    exist_ok=True
                )

                async with aiofiles.open(
                        settings["MEMBERS_LISTS_FILE_PATH"], "w",
                        encoding="utf8"
                ) as members_lists_write_file:
                    await members_lists_write_file.write(
                        json.dumps(members_lists_dict)
                    )

                await interaction.response.edit_message(view=self)

            elif button.style == ButtonStyle.green or str(button.emoji) == emoji.emojize(
                    ":raised_hand:",
                    language="alias"
            ):
                button.style = ButtonStyle.red
                button.label = "Opt-out of introduction reminders"
                button.emoji = PartialEmoji.from_str(emoji.emojize(":no_good:", language="alias"))

                if interaction_member is None:
                    await interaction.response.send_message(
                        ":warning:There was an error when trying to opt back in to interaction reminders.:warning:\n`You must be a member of the CSS Discord server to opt back in to interaction reminders.`",
                        ephemeral=True
                    )
                    return

                if await aiofiles.os.path.isfile(settings["MEMBERS_LISTS_FILE_PATH"]) and str(
                        interaction_member.id
                ) in opted_out_members:
                    opted_out_members.discard(str(interaction_member.id))

                    members_lists_dict["opted_out_members"] = list(opted_out_members)

                    async with aiofiles.open(
                            settings["MEMBERS_LISTS_FILE_PATH"], "w",
                            encoding="utf8"
                    ) as members_lists_write_file:
                        await members_lists_write_file.write(
                            json.dumps(members_lists_dict)
                        )

                await interaction.response.edit_message(view=self)


def setup(bot: TeXBot):
    bot.add_cog(Tasks_Cog(bot))
