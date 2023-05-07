import logging

import discord
from discord import Guild, Role, TextChannel
from discord.ext import commands

from exceptions import ChannelDoesNotExist, GuildDoesNotExist, RoleDoesNotExist
from main import TeXBot
from setup import settings


class Events(commands.Cog):
    def __init__(self, bot: TeXBot):
        self.bot: TeXBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guild: Guild | None = self.bot.get_guild(settings["DISCORD_GUILD_ID"])
        if guild is None:
            raise GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"])
        else:
            self.bot._css_guild = guild

        committee_role: Role | None = discord.utils.get(guild.roles, name="Committee")
        if committee_role is None:
            raise RoleDoesNotExist(role_name="Committee")
        else:
            self.bot._committee_role = committee_role

        roles_channel: TextChannel | None = discord.utils.get(guild.text_channels, name="roles")
        if roles_channel is None:
            # noinspection SpellCheckingInspection
            raise ChannelDoesNotExist(message="\"#roles\" channel must exist in order to use the \"/writeroles\" command.", channel_name="roles")
        else:
            self.bot._roles_channel = roles_channel

        logging.info(f"Ready! Logged in as {self.bot.user}")


def setup(bot: TeXBot):
    bot.add_cog(Events(bot))
