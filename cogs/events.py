import logging
import traceback

import discord
from discord import Guild, Role, TextChannel
from discord.ext import commands

from exceptions import CommitteeRoleDoesNotExist, GeneralChannelDoesNotExist, GuestRoleDoesNotExist, GuildDoesNotExist, RolesChannelDoesNotExist
from main import TeXBot
from setup import settings


class Events(commands.Cog):
    def __init__(self, bot: TeXBot):
        self.bot: TeXBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guild: Guild | None = self.bot.get_guild(settings["DISCORD_GUILD_ID"])
        if guild is None:
            try:
                raise GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"])
            except GuildDoesNotExist as css_guild_error:
                traceback.print_exception(css_guild_error)
                await self.bot.close()
                raise
        else:
            self.bot._css_guild = guild

        errors: set[Exception] = set()

        committee_role: Role | None = discord.utils.get(guild.roles, name="Committee")
        if committee_role is None:
            try:
                # noinspection SpellCheckingInspection
                raise CommitteeRoleDoesNotExist()
            except CommitteeRoleDoesNotExist as committee_role_error:
                errors.add(committee_role_error)
        else:
            self.bot._committee_role = committee_role

        guest_role: Role | None = discord.utils.get(guild.roles, name="Guest")
        if guest_role is None:
            try:
                raise GuestRoleDoesNotExist()
            except GuestRoleDoesNotExist as guest_role_error:
                errors.add(guest_role_error)
        else:
            self.bot._guest_role = guest_role

        roles_channel: TextChannel | None = discord.utils.get(guild.text_channels, name="roles")
        if roles_channel is None:
            try:
                # noinspection SpellCheckingInspection
                raise RolesChannelDoesNotExist()
            except RolesChannelDoesNotExist as roles_channel_error:
                errors.add(roles_channel_error)
        else:
            self.bot._roles_channel = roles_channel

        general_channel: TextChannel | None = discord.utils.get(guild.text_channels, name="general")
        if general_channel is None:
            try:
                # noinspection SpellCheckingInspection
                raise GeneralChannelDoesNotExist()
            except GeneralChannelDoesNotExist as general_channel_error:
                errors.add(general_channel_error)
        else:
            self.bot._general_channel = general_channel

        if errors:
            error: Exception
            for error in errors:
                traceback.print_exception(error)

            await self.bot.close()

        logging.info(f"Ready! Logged in as {self.bot.user}")


def setup(bot: TeXBot):
    bot.add_cog(Events(bot))
