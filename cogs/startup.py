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
from config.constants import DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME
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

    def _setup_discord_log_channel(self) -> None:
        NO_DISCORD_LOG_CHANNEL_SET_MESSAGE: Final[str] = (
            "Discord log-channel webhook-URL was not set, "
            "so error logs will not be sent to the Discord log-channel."
        )

        discord_logging_handlers: set[DiscordHandler] = {
            handler for handler in logger.handlers if isinstance(handler, DiscordHandler)
        }

        if len(discord_logging_handlers) > 1:
            CANNOT_DETERMINE_LOGGING_HANDLER_MESSAGE: Final[str] = (
                "Cannot determine which logging Discord-webhook-handler to update."
            )
            raise ValueError(CANNOT_DETERMINE_LOGGING_HANDLER_MESSAGE)

        if len(discord_logging_handlers) == 1:
            existing_discord_logging_handler: DiscordHandler = discord_logging_handlers.pop()

            logger.removeHandler(existing_discord_logging_handler)

            if settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]:
                new_discord_logging_handler: DiscordHandler = DiscordHandler(
                    (
                        existing_discord_logging_handler.name
                        if existing_discord_logging_handler.name != DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME  # noqa: E501
                        else (
                            self.tex_bot.user.name
                            if self.tex_bot.user
                            else DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME)
                    ),
                    settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"],
                    avatar_url=(
                        self.tex_bot.user.avatar.url
                        if self.tex_bot.user and self.tex_bot.user.avatar
                        else None
                    ),
                )
                new_discord_logging_handler.setLevel(existing_discord_logging_handler.level)
                new_discord_logging_handler.setFormatter(
                    existing_discord_logging_handler.formatter,
                )
                new_discord_logging_handler.avatar_url = new_discord_logging_handler.avatar_url

                logger.addHandler(new_discord_logging_handler)

            else:
                logger.warning(NO_DISCORD_LOG_CHANNEL_SET_MESSAGE)

        elif len(discord_logging_handlers) == 0 or not settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]:  # noqa: E501
            logger.warning(NO_DISCORD_LOG_CHANNEL_SET_MESSAGE)

        else:
            raise ValueError

    async def _initialise_main_guild(self) -> None:
        try:
            main_guild: discord.Guild | None = self.tex_bot.main_guild
        except GuildDoesNotExistError:
            main_guild = self.tex_bot.get_guild(settings["_DISCORD_MAIN_GUILD_ID"])
            if main_guild:
                self.tex_bot.set_main_guild(main_guild)

        if not main_guild:
            if self.tex_bot.application_id:
                logger.info(
                    "Invite URL: %s",
                    utils.generate_invite_url(
                        self.tex_bot.application_id,
                        settings["_DISCORD_MAIN_GUILD_ID"]),
                    )
            logger.critical(GuildDoesNotExistError(
                guild_id=settings["_DISCORD_MAIN_GUILD_ID"]),
            )
            await self.tex_bot.close()

    async def _check_strike_performed_manually_warning_location_exists(self) -> None:
        if settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"] == "DM":
            return

        STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION_EXISTS: Final[bool] = bool(
            discord.utils.get(
                self.tex_bot.main_guild.text_channels,
                name=settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"],
            )  # noqa: COM812
        )
        if STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION_EXISTS:
            return

        logger.critical(
            (
                "The channel %s does not exist, so cannot be used as the location "
                "for sending manual-moderation warning messages"
            ),
            repr(settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"]),
        )

        strike_performed_manually_warning_location_similar_to_dm: bool = (
            settings["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"].lower()
            in ("dm", "dms")
        )
        if strike_performed_manually_warning_location_similar_to_dm:
            logger.info(
                (
                    "If you meant to set the location "
                    "for sending manual-moderation warning messages to be "
                    "the DMs of the committee member that applied "
                    "the manual moderation action, use the value of %s"
                ),
                repr("DM"),
            )

        await self.tex_bot.close()

    async def _check_all_shortcut_accessors(self) -> None:
        main_guild: discord.Guild = self.tex_bot.main_guild

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

        await self._check_strike_performed_manually_warning_location_exists()

    @TeXBotBaseCog.listener()
    async def on_ready(self) -> None:
        """
        Populate the shortcut accessors of TeX-Bot after initialisation.

        Shortcut accessors should only be populated once TeX-Bot is ready to make API requests.
        """
        self._setup_discord_log_channel()

        await self._initialise_main_guild()

        if self.tex_bot.application_id:
            logger.debug(
                "Invite URL: %s",
                utils.generate_invite_url(
                    self.tex_bot.application_id,
                    settings["_DISCORD_MAIN_GUILD_ID"]),
            )

        await self._check_all_shortcut_accessors()

        logger.info("Ready! Logged in as %s", self.tex_bot.user)
