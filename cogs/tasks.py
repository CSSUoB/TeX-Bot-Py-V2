import datetime
import logging
from datetime import timedelta

import discord
import emoji
from discord import ActionRow, Button, ChannelType, Forbidden, Guild, Member, PartialEmoji, PartialMessageable, Role
from discord import ButtonStyle, Interaction, ui
from discord.ext import tasks
from discord.ui import View
from django.core.exceptions import ValidationError  # type: ignore

from cogs.utils import Bot_Cog
from db.core.models import Discord_Reminder, Interaction_Reminder_Opt_Out_Member
from exceptions import GuestRoleDoesNotExist, GuildDoesNotExist
from setup import settings
from utils import TeXBot


class Tasks_Cog(Bot_Cog):
    def __init__(self, bot: TeXBot) -> None:
        if settings["SEND_INTRODUCTION_REMINDERS"]:
            self.introduction_reminder.start()

        if settings["KICK_NO_INTRODUCTION_MEMBERS"]:
            self.kick_no_introduction_members.start()

        self.clear_reminder_backlog.start()

        super().__init__(bot)

    def cog_unload(self):
        self.introduction_reminder.cancel()
        self.kick_no_introduction_members.cancel()
        self.clear_reminder_backlog.cancel()

    @tasks.loop(minutes=15)
    async def clear_reminder_backlog(self):
        reminder: Discord_Reminder
        async for reminder in Discord_Reminder.objects.all():
            if (discord.utils.utcnow() - reminder.send_datetime) > datetime.timedelta(minutes=15):
                for user in self.bot.users:
                    if not user.bot and Discord_Reminder.hash_member_id(user.id) == reminder.hashed_member_id:
                        channel: PartialMessageable = self.bot.get_partial_messageable(
                            reminder.channel_id,
                            type=ChannelType(reminder.channel_type)
                        )

                        user_mention: str | None = None
                        if channel.type in {ChannelType.text, ChannelType.group, ChannelType.public_thread, ChannelType.private_thread}:
                            user_mention = user.mention

                        elif channel.type != ChannelType.private:
                            logging.critical(
                                ValueError("Reminder's channel_id must refer to a valid text channel/DM.")
                            )
                            await self.bot.close()
                            return

                        await channel.send(
                            f"**Sorry it's a bit late! (I'm just catching up with some reminders I missed!)**\n\n{reminder.format_message(user_mention)}"
                        )

                        await reminder.adelete()

    @clear_reminder_backlog.before_loop
    async def before_clear_reminder_backlog(self):
        await self.bot.wait_until_ready()

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

        member: Member
        for member in guild.members:
            if guest_role in member.roles or member.bot:
                continue

            if not await Interaction_Reminder_Opt_Out_Member.objects.filter(hashed_member_id=Interaction_Reminder_Opt_Out_Member.hash_member_id(member.id)).aexists():
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

        @ui.button(label="Opt-out of introduction reminders", custom_id="opt_out_introduction_reminders_button", style=ButtonStyle.red, emoji=PartialEmoji.from_str(emoji.emojize(":no_good:", language="alias")))
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

            interaction_member: Member | None = guild.get_member(interaction.user.id)

            if button.style == ButtonStyle.red or str(button.emoji) == emoji.emojize(":no_good:", language="alias") or (button.label and "Opt-out" in button.label):
                if interaction_member is None:
                    await interaction.response.send_message(
                        ":warning:There was an error when trying to opt-out of interaction reminders.:warning:\n`You must be a member of the CSS Discord server to opt-out of interaction reminders.`",
                        ephemeral=True
                    )
                    return

                try:
                    await Interaction_Reminder_Opt_Out_Member.objects.acreate(
                        member_id=interaction_member.id
                    )
                except ValidationError as create_interaction_reminder_opt_out_member_error:
                    if "hashed_member_id" not in create_interaction_reminder_opt_out_member_error.message_dict or all("already exists" not in error for error in create_interaction_reminder_opt_out_member_error.message_dict["hashed_member_id"]):
                        raise

                button.style = ButtonStyle.green
                button.label = "Opt back in to introduction reminders"
                button.emoji = PartialEmoji.from_str(emoji.emojize(":raised_hand:", language="alias"))

                await interaction.response.edit_message(view=self)

            elif button.style == ButtonStyle.green or str(button.emoji) == emoji.emojize(":raised_hand:", language="alias") or (button.label and "Opt back in" in button.label):
                if interaction_member is None:
                    await interaction.response.send_message(
                        ":warning:There was an error when trying to opt back in to interaction reminders.:warning:\n`You must be a member of the CSS Discord server to opt back in to interaction reminders.`",
                        ephemeral=True
                    )
                    return

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

                button.style = ButtonStyle.red
                button.label = "Opt-out of introduction reminders"
                button.emoji = PartialEmoji.from_str(emoji.emojize(":no_good:", language="alias"))

                await interaction.response.edit_message(view=self)


def setup(bot: TeXBot):
    bot.add_cog(Tasks_Cog(bot))
