import logging

import discord
from discord import Guild, Role, TextChannel, Member
from discord.ext import commands

from cogs.utils import Bot_Cog
from db.core.models import Interaction_Reminder_Opt_Out_Member
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

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        try:
            guild: Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        if before.guild != guild or after.guild != guild:
            return

        guest_role: Role | None = self.bot.guest_role
        if guest_role is None:
            logging.critical(GuestRoleDoesNotExist())
            await self.bot.close()
            return

        if guest_role not in before.roles and guest_role in after.roles:
            try:
                interaction_reminder_opt_out_member: Interaction_Reminder_Opt_Out_Member = await Interaction_Reminder_Opt_Out_Member.objects.aget(
                    hashed_member_id=Interaction_Reminder_Opt_Out_Member.hash_member_id(
                        before.id
                    )
                )
            except Interaction_Reminder_Opt_Out_Member.DoesNotExist:
                pass
            else:
                await interaction_reminder_opt_out_member.adelete()

            async for message in after.history():
                if "joined the CSS Discord server but have not yet introduced" in message.content and message.author.bot:
                    await message.delete(
                        reason="Delete interaction reminders after user is inducted."
                    )

            welcome_channel_mention: str = "`#welcome`"
            welcome_channel: TextChannel | None = self.bot.welcome_channel
            if welcome_channel:
                welcome_channel_mention = welcome_channel.mention

            roles_channel_mention: str = "`#roles`"
            roles_channel: TextChannel | None = self.bot.roles_channel
            if roles_channel:
                roles_channel_mention = roles_channel.mention

            await after.send(
                f"**Congrats on joining the CSS Discord server as a guest!** You now have access to contribute to all the public channels.\n\nSome things to do to get started:\n1. Check out our rules in {welcome_channel_mention}\n2. Head to {roles_channel_mention} and click on the icons to get optional roles like pronouns and year groups\n3. Change your nickname to whatever you wish others to refer to you as (You can do this by right-clicking your name in the members list to the right & selecting \"Edit Server Profile\")"
            )


def setup(bot: TeXBot):
    bot.add_cog(Events_Cog(bot))
