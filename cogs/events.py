import logging

import discord
from discord import Guild, Role, TextChannel
from discord.ext import commands

from cogs.utils import Bot_Cog
from exceptions import CommitteeRoleDoesNotExist, GeneralChannelDoesNotExist, GuestRoleDoesNotExist, GuildDoesNotExist, MemberRoleDoesNotExist, RolesChannelDoesNotExist
from setup import settings
from utils import TeXBot
from .tasks import Tasks_Cog


class Events_Cog(Bot_Cog):
    @commands.Cog.listener()
    async def on_ready(self):
        guild: Guild | None = self.bot.get_guild(settings["DISCORD_GUILD_ID"])
        if guild is None:
            logging.critical(GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"]))
            await self.bot.close()
            return
        else:
            self.bot._css_guild = guild

        committee_role: Role | None = discord.utils.get(guild.roles, name="Committee")
        if committee_role is None:
            logging.warning(CommitteeRoleDoesNotExist())

        guest_role: Role | None = discord.utils.get(guild.roles, name="Guest")
        if guest_role is None:
            logging.warning(GuestRoleDoesNotExist())

        member_role: Role | None = discord.utils.get(guild.roles, name="Member")
        if member_role is None:
            logging.warning(MemberRoleDoesNotExist())

        roles_channel: TextChannel | None = discord.utils.get(guild.text_channels, name="roles")
        if roles_channel is None:
            logging.warning(RolesChannelDoesNotExist())

        general_channel: TextChannel | None = discord.utils.get(guild.text_channels, name="general")
        if general_channel is None:
            logging.warning(GeneralChannelDoesNotExist())

        self.bot.add_view(
            Tasks_Cog.Opt_Out_Introduction_Reminders_View(self.bot)
        )

        logging.info(f"Ready! Logged in as {self.bot.user}")


def setup(bot: TeXBot):
    bot.add_cog(Events_Cog(bot))
