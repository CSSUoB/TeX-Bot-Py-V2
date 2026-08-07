"""Contains cog classes for any startup interactions."""

import logging
from typing import TYPE_CHECKING

import discord

import utils
from config import settings
from exceptions import (
    ArchivistRoleDoesNotExistError,
    CommitteeRoleDoesNotExistError,
    GeneralChannelDoesNotExistError,
    GuestRoleDoesNotExistError,
    GuildDoesNotExistError,
    MemberRoleDoesNotExistError,
    MSLMembershipError,
    RolesChannelDoesNotExistError,
)
from utils import TeXBotBaseCog
from utils.msl import fetch_community_group_members_list, msl_is_configured

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

__all__: "Sequence[str]" = ("StartupCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class StartupCog(TeXBotBaseCog):
    """Cog class that defines additional code to execute upon startup."""

    @TeXBotBaseCog.listener()
    async def on_ready(self) -> None:
        """
        Populate the shortcut accessors of TeX-Bot after initialisation.

        Shortcut accessors should only be populated once TeX-Bot is ready to make API requests.
        """
        # NOTE: Relaying error logs to a Discord log channel is set up from the loaded
        # configuration (& re-applied upon every reload), rather than here. Attaching a
        # handler here as well would relay every error twice, & once more for every
        # gateway re-identify, because this listener runs again upon each reconnection.

        try:
            main_guild: discord.Guild | None = self.bot.main_guild
        except GuildDoesNotExistError:
            main_guild = self.bot.get_guild(settings.discord.main_guild_id)
            if main_guild:
                self.bot.set_main_guild(main_guild)

        if not main_guild:
            if self.bot.application_id:
                logger.info(
                    "Invite URL: %s",
                    utils.generate_invite_url(
                        self.bot.application_id, settings.discord.main_guild_id
                    ),
                )
            logger.critical(GuildDoesNotExistError(guild_id=settings.discord.main_guild_id))
            await self.bot.close()

        if self.bot.application_id:
            logger.debug(
                "Invite URL: %s",
                utils.generate_invite_url(
                    self.bot.application_id, settings.discord.main_guild_id
                ),
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

        if not msl_is_configured():
            logger.warning(
                "Both 'community-group:msl:organisation-id' & "
                "'community-group:msl:auth-cookie' must be set for your group's "
                "members-list to be retrieved. Every feature that depends upon knowing "
                "who holds a membership will not work until they are."
            )
        else:
            try:
                await fetch_community_group_members_list()
            except MSLMembershipError as msl_membership_error:
                logger.debug(
                    "Failed to update community group member list cache on startup: %s",
                    msl_membership_error,
                )

        if settings.commands.strike.performed_manually_warning_location != "DM":
            manual_moderation_warning_message_location_exists: bool = bool(
                discord.utils.get(
                    main_guild.text_channels,
                    name=settings.commands.strike.performed_manually_warning_location,
                )
            )
            if not manual_moderation_warning_message_location_exists:
                logger.critical(
                    (
                        "The channel %s does not exist, so cannot be used as the location "
                        "for sending manual-moderation warning messages"
                    ),
                    repr(settings.commands.strike.performed_manually_warning_location),
                )
                manual_moderation_warning_message_location_similar_to_dm: bool = (
                    settings.commands.strike.performed_manually_warning_location.lower()
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
