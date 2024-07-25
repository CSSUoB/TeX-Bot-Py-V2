"""Contains cog classes for any startup interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("StartupCog",)


import logging
from logging import Logger
from typing import Final

import discord
from discord_logging.handler import DiscordHandler

import utils
from config import settings
from exceptions import (
    ArchivistRoleDoesNotExistError,
    CommitteeRoleDoesNotExistError,
    GeneralChannelDoesNotExistError,
    GuestRoleDoesNotExistError,
    GuildDoesNotExistError,
    MemberRoleDoesNotExistError,
    RolesChannelDoesNotExistError,
)
from utils import TeXBotBaseCog

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class StartupCog(TeXBotBaseCog):
    """Cog class that defines additional code to execute upon startup."""

    @TeXBotBaseCog.listener()
    async def on_ready(self) -> None:
        """
        Populate the shortcut accessors of TeX-Bot after initialisation.

        Shortcut accessors should only be populated once TeX-Bot is ready to make API requests.
        """
        if settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]:
            discord_logging_handler: logging.Handler = DiscordHandler(
                self.bot.user.name if self.bot.user else "TeXBot",
                settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"],
                avatar_url=(
                    self.bot.user.avatar.url
                    if self.bot.user and self.bot.user.avatar
                    else None
                ),
            )
            discord_logging_handler.setLevel(logging.WARNING)
            # noinspection SpellCheckingInspection
            discord_logging_handler.setFormatter(
                logging.Formatter("{levelname} | {message}", style="{"),
            )

            logger.addHandler(discord_logging_handler)

        else:
            logger.warning(
                "DISCORD_LOG_CHANNEL_WEBHOOK_URL was not set, "
                "so error logs will not be sent to the Discord log channel.",
            )

        try:
            main_guild: discord.Guild | None = self.bot.main_guild
        except GuildDoesNotExistError:
            main_guild = self.bot.get_guild(settings["_DISCORD_MAIN_GUILD_ID"])
            if main_guild:
                self.bot.set_main_guild(main_guild)

        if not main_guild:
            if self.bot.application_id:
                logger.info(
                    "Invite URL: %s",
                    utils.generate_invite_url(
                        self.bot.application_id,
                        settings["_DISCORD_MAIN_GUILD_ID"]),
                    )
            logger.critical(GuildDoesNotExistError(
                guild_id=settings["_DISCORD_MAIN_GUILD_ID"]),
            )
            await self.bot.close()

        if self.bot.application_id:
            logger.debug(
                "Invite URL: %s",
                utils.generate_invite_url(
                    self.bot.application_id,
                    settings["_DISCORD_MAIN_GUILD_ID"]),
            )

        if not discord.utils.get(main_guild.roles, name="Committee"):
            logger.warning(CommitteeRoleDoesNotExistError())

        if not discord.utils.get(main_guild.roles, name="Guest"):
            logger.warning(GuestRoleDoesNotExistError())

        if not discord.utils.get(main_guild.roles, name="Member"):
            logger.warning(MemberRoleDoesNotExistError())

        if not discord.utils.get(main_guild.roles, name="Archivist"):
            logger.warning(ArchivistRoleDoesNotExistError())

        if not discord.utils.get(main_guild.text_channels, name="roles"):
            logger.warning(RolesChannelDoesNotExistError())

        if not discord.utils.get(main_guild.text_channels, name="general"):
            logger.warning(GeneralChannelDoesNotExistError())

        if settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"] != "DM":
            manual_moderation_warning_message_location_exists: bool = bool(
                discord.utils.get(
                    main_guild.text_channels,
                    name=settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"],
                ),
            )
            if not manual_moderation_warning_message_location_exists:
                logger.critical(
                    (
                        "The channel %s does not exist, so cannot be used as the location "
                        "for sending manual-moderation warning messages"
                    ),
                    repr(settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"]),
                )
                manual_moderation_warning_message_location_similar_to_dm: bool = (
                    settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"].lower()
                    in ("dm", "dms")
                )
                if manual_moderation_warning_message_location_similar_to_dm:
                    logger.info(
                        (
                            "If you meant to set the location "
                            "for sending manual-moderation warning messages to be "
                            "the DMs of the committee member that applied "
                            "the manual moderation action, use the value of %s"
                        ),
                        repr("DM"),
                    )
                await self.bot.close()

        logger.info("Ready! Logged in as %s", self.bot.user)
