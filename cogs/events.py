import logging
from logging import Logger

import discord
from discord import TextChannel
from discord.ext import commands

from cogs.utils import Bot_Cog
from db.core.models import InteractionReminderOptOutMember, LeftMember
from exceptions import ArchivistRoleDoesNotExist, CommitteeRoleDoesNotExist, GeneralChannelDoesNotExist, GuestRoleDoesNotExist, GuildDoesNotExist, MemberRoleDoesNotExist, RolesChannelDoesNotExist
from config import settings
from utils import DiscordLoggingHandler, TeXBot
from .tasks import Tasks_Cog


class Events_Cog(Bot_Cog):
    @commands.Cog.listener()
    async def on_ready(self):
        guild: discord.Guild | None = self.bot.get_guild(settings["DISCORD_GUILD_ID"])
        if not guild:
            logging.critical(GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"]))
            await self.bot.close()
            return
        else:
            self.bot._css_guild = guild

        log_channel: TextChannel | None
        if settings["DISCORD_LOG_CHANNEL_ID"] and (log_channel := discord.utils.get(guild.text_channels, id=settings["DISCORD_LOG_CHANNEL_ID"])):
            discord_logging_handler: DiscordLoggingHandler = DiscordLoggingHandler(log_channel)
            discord_logging_handler.setLevel(logging.WARNING)
            root_logger: Logger = logging.getLogger("")
            root_logger_handler: logging.Handler
            for root_logger_handler in root_logger.handlers:
                if hasattr(root_logger_handler, "formatter"):
                    discord_logging_handler.setFormatter(root_logger_handler.formatter)
                    break
            root_logger.addHandler(discord_logging_handler)
        else:
            logging.warning("DISCORD_LOG_CHANNEL_ID was not set, so error logs will not be sent to the Discord log channel.")

        if not discord.utils.get(guild.roles, name="Committee"):
            logging.warning(CommitteeRoleDoesNotExist())

        if not discord.utils.get(guild.roles, name="Guest"):
            logging.warning(GuestRoleDoesNotExist())

        if not discord.utils.get(guild.roles, name="Member"):
            logging.warning(MemberRoleDoesNotExist())

        if not discord.utils.get(guild.roles, name="Archivist"):
            logging.warning(ArchivistRoleDoesNotExist())

        if not discord.utils.get(guild.text_channels, name="roles"):
            logging.warning(RolesChannelDoesNotExist())

        if not discord.utils.get(guild.text_channels, name="general"):
            logging.warning(GeneralChannelDoesNotExist())

        self.bot.add_view(
            Tasks_Cog.Opt_Out_Introduction_Reminders_View(self.bot)
        )

        logging.info(f"Ready! Logged in as {self.bot.user}")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        if before.guild != guild or after.guild != guild or before.bot or after.bot:
            return

        guest_role: discord.Role | None = self.bot.guest_role
        if not guest_role:
            logging.critical(GuestRoleDoesNotExist())
            await self.bot.close()
            return

        if guest_role not in before.roles and guest_role in after.roles:
            try:
                interaction_reminder_opt_out_member: InteractionReminderOptOutMember = await InteractionReminderOptOutMember.objects.aget(
                    hashed_member_id=InteractionReminderOptOutMember.hash_member_id(
                        before.id
                    )
                )
            except InteractionReminderOptOutMember.DoesNotExist:
                pass
            else:
                await interaction_reminder_opt_out_member.adelete()

            async for message in after.history():
                if "joined the CSS Discord server but have not yet introduced" in message.content and message.author.bot:
                    await message.delete(
                        reason="Delete interaction reminders after user is inducted."
                    )

            welcome_channel_mention: str = "`#welcome`"
            welcome_channel: discord.TextChannel | None = self.bot.welcome_channel
            if welcome_channel:
                welcome_channel_mention = welcome_channel.mention

            roles_channel_mention: str = "`#roles`"
            roles_channel: discord.TextChannel | None = self.bot.roles_channel
            if roles_channel:
                roles_channel_mention = roles_channel.mention

            await after.send(
                f"**Congrats on joining the CSS Discord server as a guest!** You now have access to contribute to all the public channels.\n\nSome things to do to get started:\n1. Check out our rules in {welcome_channel_mention}\n2. Head to {roles_channel_mention} and click on the icons to get optional roles like pronouns and year groups\n3. Change your nickname to whatever you wish others to refer to you as (You can do this by right-clicking your name in the members list to the right & selecting \"Edit Server Profile\")"
            )

    @commands.Cog.listener()
    async def on_member_leave(self, member: discord.Member):
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        if member.guild != guild or member.bot:
            return

        await LeftMember.objects.acreate(roles={f"@{role.name}" for role in member.roles if role.name != "@everyone"})


def setup(bot: TeXBot):
    bot.add_cog(Events_Cog(bot))
