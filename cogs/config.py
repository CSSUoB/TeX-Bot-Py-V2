"""Contains cog classes for viewing & changing TeX-Bot's configuration at run-time."""

import logging
from typing import TYPE_CHECKING

import discord

import config
from config import SettingsValidationError, get_settings_metadata
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from config import ConfigSettingMetadata
    from utils import TeXBot, TeXBotApplicationContext


__all__: "Sequence[str]" = ("ConfigCommandsCog", "reload_config")


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

MAXIMUM_LISTED_SETTINGS: "Final[int]" = 20


async def reload_config(bot: "TeXBot") -> "tuple[AbstractSet[str], AbstractSet[str]]":
    """
    Reload the configuration file, applying every change that can be applied while running.

    Returns the set of settings key paths that changed, along with the subset of those
    that cannot take effect until TeX-Bot is restarted.

    Raises `SettingsValidationError` (or one of the file-reading errors) without applying
    anything, if the configuration file cannot be read or contains invalid settings.
    """
    CHANGED_SETTINGS: Final[AbstractSet[str]] = config.reload_settings()

    if not CHANGED_SETTINGS:
        return CHANGED_SETTINGS, frozenset()

    # NOTE: Every cog is offered the change, so that a cog holding a copy of any setting
    # (the interval of a task, for example) can re-apply it to itself.
    cog: discord.Cog
    for cog in bot.cogs.values():
        if isinstance(cog, TeXBotBaseCog):
            await cog.on_config_reloaded(CHANGED_SETTINGS)

    SETTINGS_METADATA: Final[Mapping[str, ConfigSettingMetadata]] = get_settings_metadata()

    RESTART_REQUIRED_SETTINGS: Final[AbstractSet[str]] = frozenset(
        changed_setting
        for changed_setting in CHANGED_SETTINGS
        if changed_setting in SETTINGS_METADATA
        and SETTINGS_METADATA[changed_setting].requires_restart
    )

    return CHANGED_SETTINGS, RESTART_REQUIRED_SETTINGS


def _format_settings_list(settings_names: "Iterable[str]") -> str:
    """Format the given settings key paths into a bulleted list, truncated if very long."""
    SORTED_SETTINGS_NAMES: Final[Sequence[str]] = sorted(settings_names)

    listed_settings_names: Sequence[str] = SORTED_SETTINGS_NAMES[:MAXIMUM_LISTED_SETTINGS]

    formatted_settings_list: str = "\n".join(
        f"- `{settings_name}`" for settings_name in listed_settings_names
    )

    REMAINING_COUNT: Final[int] = len(SORTED_SETTINGS_NAMES) - len(listed_settings_names)
    if REMAINING_COUNT > 0:
        formatted_settings_list += f"\n- _...and {REMAINING_COUNT} more_"

    return formatted_settings_list


class ConfigCommandsCog(TeXBotBaseCog):
    """Cog class that defines the "/config" command group & its call-back methods."""

    config: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="config",
        description="View & change TeX-Bot's configuration.",
    )

    @config.command(
        name="reload",
        description="Reload the configuration file, applying any changes made to it.",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def reload(self, ctx: "TeXBotApplicationContext") -> None:
        """
        Definition & callback response of the "config reload" command.

        Reads the configuration file again, applying every change that can be applied
        without restarting TeX-Bot, and reporting any that cannot.
        """
        await ctx.defer(ephemeral=True)

        changed_settings: AbstractSet[str]
        restart_required_settings: AbstractSet[str]

        configuration_error: Exception
        try:
            changed_settings, restart_required_settings = await reload_config(self.bot)
        except SettingsValidationError as configuration_error:
            logger.warning("Configuration reload rejected:\n%s", configuration_error)
            await ctx.respond(
                (
                    ":x: The configuration file was **not** loaded, "
                    "because it contains invalid settings. "
                    "No changes have been applied.\n"
                    f"```\n{configuration_error}\n```"
                ),
                ephemeral=True,
            )
            return
        except (OSError, ValueError) as configuration_error:
            logger.warning("Configuration reload failed: %s", configuration_error)
            await ctx.respond(
                (
                    ":x: The configuration file could not be read, "
                    "so no changes have been applied.\n"
                    f"```\n{configuration_error}\n```"
                ),
                ephemeral=True,
            )
            return

        if not changed_settings:
            await ctx.respond(
                ":information_source: The configuration file has not changed.",
                ephemeral=True,
            )
            return

        logger.info("Configuration reloaded: %s setting(s) changed.", len(changed_settings))

        response_message: str = (
            f":white_check_mark: Reloaded the configuration file. "
            f"{len(changed_settings)} setting(s) changed:\n"
            f"{_format_settings_list(changed_settings)}"
        )

        if restart_required_settings:
            response_message += (
                "\n\n:warning: **TeX-Bot must be restarted "
                "before the following take effect:**\n"
                f"{_format_settings_list(restart_required_settings)}\n"
                "Every other change above has already been applied."
            )

        await ctx.respond(response_message, ephemeral=True)
