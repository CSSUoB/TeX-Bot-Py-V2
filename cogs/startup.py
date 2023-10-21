"""Contains cog classes for any startup interactions."""

import logging

import discord
from discord_logging.handler import DiscordHandler

from cogs._utils import TeXBotCog
from config import settings
from exceptions import (
    ArchivistRoleDoesNotExist,
    CommitteeRoleDoesNotExist,
    GeneralChannelDoesNotExist,
    GuestRoleDoesNotExist,
    GuildDoesNotExist,
    MemberRoleDoesNotExist,
    RolesChannelDoesNotExist,
)


class StartupCog(TeXBotCog):
    """Cog class that defines additional code to execute upon startup."""

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

        if settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] != "DM":
            manual_moderation_warning_message_location_exists: bool = bool(
                discord.utils.get(
                    guild.text_channels,
                    name=settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"]
                )
            )
            if not manual_moderation_warning_message_location_exists:
                logging.critical(
                    (
                        "The channel %s does not exist, so cannot be used as the location"
                        " for sending manual-moderation warning messages"
                    ),
                    repr(settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"])
                )
                manual_moderation_warning_message_location_similar_to_dm: bool = (
                    settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"].lower()
                    in ("dm", "dms")
                )
                if manual_moderation_warning_message_location_similar_to_dm:
                    logging.info(
                        (
                            "If you meant to set the location"
                            " for sending manual-moderation warning messages to be"
                            " the DMs of the committee member that applied"
                            " the manual moderation action, use the value of %s"
                        ),
                        repr("DM")
                    )
                await self.bot.close()
                return

        logging.info("Ready! Logged in as %s", self.bot.user)
