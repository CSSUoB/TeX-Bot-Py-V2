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
            raise ValueError(
                "Cannot determine which logging Discord-webhook-handler to update."
            )

        elif len(discord_logging_handlers) == 1:
            existing_discord_logging_handler: DiscordHandler = discord_logging_handlers.pop()

            logger.removeHandler(existing_discord_logging_handler)

            if settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]:
                new_discord_logging_handler: DiscordHandler = DiscordHandler(
                    (
                        existing_discord_logging_handler.name
                        if existing_discord_logging_handler.name != DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME  # noqa: E501
                        else (
                            self.bot.user.name
                            if self.bot.user
                            else DEFAULT_DISCORD_LOGGING_HANDLER_DISPLAY_NAME)
                    ),
                    settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"],
                    avatar_url=(
                        self.bot.user.avatar.url
                        if self.bot.user and self.bot.user.avatar
                        else None
                    ),
                )
                new_discord_logging_handler.setLevel(existing_discord_logging_handler.level)
                new_discord_logging_handler.setFormatter(
                    existing_discord_logging_handler.formatter
                )
                new_discord_logging_handler.avatar_url = new_discord_logging_handler.avatar_url

                logger.addHandler(new_discord_logging_handler)

            else:
                logger.warning(NO_DISCORD_LOG_CHANNEL_SET_MESSAGE)

        elif len(discord_logging_handlers) == 0 or not settings["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]:  # noqa: E501
            logger.warning(NO_DISCORD_LOG_CHANNEL_SET_MESSAGE)

        else:
            raise ValueError

    async def _get_main_guild(self) -> discord.Guild:
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
                guild_id=settings["_DISCORD_MAIN_GUILD_ID"])
            )
            await self.bot.close()
            raise RuntimeError

        return main_guild

    @TeXBotBaseCog.listener()
    async def on_ready(self) -> None:
        """
        Populate the shortcut accessors of the bot after initialisation.

        Shortcut accessors should only be populated once the bot is ready to make API requests.
        """
        self._setup_discord_log_channel()

        main_guild: discord.Guild = await self._get_main_guild()

        if self.bot.application_id:
            logger.debug(
                "Invite URL: %s",
                utils.generate_invite_url(
                    self.bot.application_id,
                    settings["_DISCORD_MAIN_GUILD_ID"]),
            )

        if not discord.utils.get(main_guild.roles, name="Committee"):  # TODO: Move to separate functions
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

        if settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] != "DM":
            manual_moderation_warning_message_location_exists: bool = bool(
                discord.utils.get(
                    main_guild.text_channels,
                    name=settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"],
                ),
            )
            if not manual_moderation_warning_message_location_exists:
                logger.critical(
                    (
                        "The channel %s does not exist, so cannot be used as the location "
                        "for sending manual-moderation warning messages"
                    ),
                    repr(settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"]),
                )
                manual_moderation_warning_message_location_similar_to_dm: bool = (
                    settings["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"].lower()
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
                return

        logger.info("Ready! Logged in as %s", self.bot.user)
