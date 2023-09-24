"""Contains event listeners for startup & events within the CSS Discord server."""

import logging

import discord
from discord_logging.handler import DiscordHandler

from cogs.utils import TeXBotCog
from config import settings
from db.core.models import IntroductionReminderOptOutMember, LeftMember
from exceptions import (
    ArchivistRoleDoesNotExist,
    CommitteeRoleDoesNotExist,
    GeneralChannelDoesNotExist,
    GuestRoleDoesNotExist,
    GuildDoesNotExist,
    MemberRoleDoesNotExist,
    RolesChannelDoesNotExist,
)
from utils import TeXBot

from .tasks import TasksCog


class EventsCog(TeXBotCog):
    """Cog container class for all listeners for the events that need to be observed."""

    @TeXBotCog.listener()
    async def on_ready(self) -> None:
        """
        Populate the shortcut accessors of the bot after initialisation.

        Shortcut accessors should only be populated once the bot is ready to make API requests.
        """
        if settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]:
            discord_logging_handler: DiscordHandler = DiscordHandler(
                self.bot.user.name if self.bot.user else "TeXBot",
                settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"],
                avatar_url=(
                    self.bot.user.avatar.url
                    if self.bot.user and self.bot.user.avatar
                    else None
                )
            )
            discord_logging_handler.setLevel(logging.WARNING)
            # noinspection SpellCheckingInspection
            discord_logging_handler.setFormatter(
                logging.Formatter("%(levelname)s | %(message)s")
            )

            logging.getLogger("").addHandler(discord_logging_handler)

        else:
            logging.warning(
                "DISCORD_LOG_CHANNEL_WEBHOOK_URL was not set,"
                " so error logs will not be sent to the Discord log channel."
            )

        guild: discord.Guild | None = self.bot.get_guild(settings["DISCORD_GUILD_ID"])
        if not guild:
            logging.critical(GuildDoesNotExist(guild_id=settings["DISCORD_GUILD_ID"]))
            await self.bot.close()
            return
        self.bot.set_css_guild(guild)

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
            TasksCog.OptOutIntroductionRemindersView(self.bot)
        )

        logging.info("Ready! Logged in as %s", self.bot.user)

    @TeXBotCog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException) -> None:  # noqa: E501
        """Log any major command errors in the logging channel & stderr."""
        await self.bot.send_error(
            ctx,
            message="Please contact a committee member.",
            command_name=ctx.command.qualified_name,
            logging_message=str(error)
        )

    @TeXBotCog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """
        Send a welcome message to this member's DMs & remove introduction reminder flags.

        These post-induction actions are only applied to users that have just been inducted as
        a guest into the CSS Discord server.
        """
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        if before.guild != guild or after.guild != guild or before.bot or after.bot:
            return

        guest_role: discord.Role | None = await self.bot.guest_role
        if not guest_role:
            logging.critical(GuestRoleDoesNotExist())
            await self.bot.close()
            return

        if guest_role not in before.roles and guest_role in after.roles:
            try:
                introduction_reminder_opt_out_member: IntroductionReminderOptOutMember = await IntroductionReminderOptOutMember.objects.aget(  # noqa: E501
                    hashed_member_id=IntroductionReminderOptOutMember.hash_member_id(
                        before.id
                    )
                )
            except IntroductionReminderOptOutMember.DoesNotExist:
                pass
            else:
                await introduction_reminder_opt_out_member.adelete()

            async for message in after.history():
                message_is_introduction_reminder: bool = (
                    (
                        "joined the CSS Discord server but have not yet introduced"
                    ) in message.content
                    and message.author.bot
                )
                if message_is_introduction_reminder:
                    await message.delete(
                        reason="Delete introduction reminders after member is inducted."
                    )

            welcome_channel_mention: str = "`#welcome`"
            welcome_channel: discord.TextChannel | None = await self.bot.welcome_channel
            if welcome_channel:
                welcome_channel_mention = welcome_channel.mention

            roles_channel_mention: str = "`#roles`"
            roles_channel: discord.TextChannel | None = await self.bot.roles_channel
            if roles_channel:
                roles_channel_mention = roles_channel.mention

            await after.send(
                "**Congrats on joining the CSS Discord server as a guest!**"
                " You now have access to contribute to all the public channels."
                "\n\nSome things to do to get started:"
                f"\n1. Check out our rules in {welcome_channel_mention}"
                f"\n2. Head to {roles_channel_mention} and click on the icons to get"
                " optional roles like pronouns and year groups"
                "\n3. Change your nickname to whatever you wish others to refer to you as"
                " (You can do this by right-clicking your name in the members list"
                " to the right & selecting \"Edit Server Profile\")"
            )
            await after.send(
                "You can also get yourself an annual membership to CSS for only £5!"
                " Just head to https://cssbham.com/join."
                " You'll get awesome perks like a free T-shirt:shirt:,"
                " access to member only events:calendar_spiral:"
                " & a cool green name on the CSS Discord server:green_square:!"
                " Checkout all the perks at https://cssbham.com/membership."
            )

    @TeXBotCog.listener()
    async def on_member_leave(self, member: discord.Member) -> None:
        """Update the stats of the roles that members had when they left the Discord server."""
        try:
            guild: discord.Guild = self.bot.css_guild
        except GuildDoesNotExist as guild_error:
            logging.critical(guild_error)
            await self.bot.close()
            return

        if member.guild != guild or member.bot:
            return

        await LeftMember.objects.acreate(
            roles={f"@{role.name}" for role in member.roles if role.name != "@everyone"}
        )


def setup(bot: TeXBot) -> None:
    """
    Add the events cog to the bot.

    This is called at startup, to load all the cogs onto the bot.
    """
    bot.add_cog(EventsCog(bot))
