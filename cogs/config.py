"""Contains cog classes for viewing & changing TeX-Bot's configuration at run-time."""

import logging
from typing import TYPE_CHECKING

import discord

import config
from config import (
    InvalidSettingsFileError,
    SettingsFileChangedError,
    SettingsFileNotFoundError,
    SettingsNotLoadedError,
    SettingsValidationError,
    UnknownSettingError,
)
from utils import CommandChecks, TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from config import ConfigReloadResult, ConfigSettingMetadata
    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext


__all__: "Sequence[str]" = ("ConfigCommandsCog",)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

MAXIMUM_LISTED_SETTINGS: "Final[int]" = 20

# NOTE: The greatest number of suggestions that Discord will display at once.
MAXIMUM_AUTOCOMPLETE_SUGGESTIONS: "Final[int]" = 25


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


def _format_restart_required_warning(restart_required_settings: "AbstractSet[str]") -> str:
    """Format the warning that a change cannot take effect until TeX-Bot is restarted."""
    if not restart_required_settings:
        return ""

    return (
        "\n\n:warning: **TeX-Bot must be restarted "
        "before the following take effect:**\n"
        f"{_format_settings_list(restart_required_settings)}"
    )


class ConfigCommandsCog(TeXBotBaseCog):
    """Cog class that defines the "/config" command group & its call-back methods."""

    config: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="config",
        description="View & change TeX-Bot's configuration.",
    )

    @staticmethod
    async def autocomplete_get_settings_names(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """
        Autocomplete callable that generates the set of configurable settings names.

        Every setting whose name contains what has been typed so far is suggested,
        rather than only those beginning with it, because each name is prefixed with the
        section holding it & so is rarely typed from its beginning.
        """
        TYPED_VALUE: Final[str] = str(ctx.value or "").strip().lower()

        MATCHING_SETTINGS_NAMES: Final[Sequence[str]] = [
            setting_name
            for setting_name in config.documented_setting_names()
            if TYPED_VALUE in setting_name.lower()
        ]

        return {
            discord.OptionChoice(name=setting_name, value=setting_name)
            # NOTE: Sliced because Discord refuses a response holding more suggestions
            # than it is willing to display.
            for setting_name in MATCHING_SETTINGS_NAMES[:MAXIMUM_AUTOCOMPLETE_SUGGESTIONS]
        }

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
            changed_settings, restart_required_settings = config.reload_settings()
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
        except (
            SettingsFileNotFoundError,
            InvalidSettingsFileError,
            OSError,
        ) as configuration_error:
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
                f"{_format_restart_required_warning(restart_required_settings)}\n"
                "Every other change above has already been applied."
            )

        await ctx.respond(response_message, ephemeral=True)

    @config.command(
        name="get",
        description="Show the current value of a single configuration setting.",
    )
    @discord.option(
        name="setting",
        description="The name of the setting to show.",
        input_type=str,
        autocomplete=autocomplete_get_settings_names,
        required=True,
        parameter_name="setting_name",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def get(self, ctx: "TeXBotApplicationContext", setting_name: str) -> None:
        """
        Definition & callback response of the "config get" command.

        Shows what a single setting is currently set to, along with what it controls.
        """
        await ctx.defer(ephemeral=True)

        setting_metadata: ConfigSettingMetadata
        try:
            setting_metadata = config.setting_metadata(setting_name)
            CURRENT_VALUE: Final[object] = config.settings.as_flat_mapping()[setting_name]
        except UnknownSettingError as unknown_setting_error:
            await self._respond_with_unknown_setting(ctx, unknown_setting_error)
            return
        except SettingsNotLoadedError:
            await ctx.respond(
                ":x: No configuration has been loaded, so no setting can be shown.",
                ephemeral=True,
            )
            return

        IS_SET_WITHIN_FILE: Final[bool] = config.settings.document.contains(
            setting_name.split(config.SETTING_NAME_SEPARATOR)
        )

        response_message: str = (
            f"**`{setting_name}`**\n"
            f"{config.format_setting_value(CURRENT_VALUE, secret=setting_metadata.secret)}"
        )

        if not IS_SET_WITHIN_FILE:
            response_message += " _(default; not set within the configuration file)_"

        if setting_metadata.description:
            response_message += f"\n\n{setting_metadata.description}"

        if setting_metadata.requires_restart:
            response_message += (
                "\n\n:warning: Changing this setting requires TeX-Bot to be restarted."
            )

        # NOTE: The value shown is the one currently in use, which is the one that was
        # loaded. Saying so is what stops an edit made to the file since then from
        # looking as though it had simply been ignored.
        if config.settings.file_has_changed():
            response_message += (
                "\n\n:warning: The configuration file has been edited since TeX-Bot "
                "last loaded it, so the value shown above may no longer match it. "
                "Run `/config reload` to load those edits."
            )

        await ctx.respond(response_message, ephemeral=True)

    @config.command(
        name="set",
        description="Change a single configuration setting, then apply the change.",
    )
    @discord.option(
        name="setting",
        description="The name of the setting to change.",
        input_type=str,
        autocomplete=autocomplete_get_settings_names,
        required=True,
        parameter_name="setting_name",
    )
    @discord.option(
        name="value",
        description="The new value, written exactly as it would be within the file.",
        input_type=str,
        required=True,
        min_length=1,
        max_length=1000,
        parameter_name="raw_value",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def set(
        self, ctx: "TeXBotApplicationContext", setting_name: str, raw_value: str
    ) -> None:
        """
        Definition & callback response of the "config set" command.

        Writes a single setting into the configuration file & applies it. The new value
        is validated first, so a value that would be rejected changes nothing at all.
        """
        await ctx.defer(ephemeral=True)

        reload_result: ConfigReloadResult
        try:
            setting_metadata: ConfigSettingMetadata = config.setting_metadata(setting_name)
            reload_result = config.set_setting(setting_name, raw_value)
        except UnknownSettingError as unknown_setting_error:
            await self._respond_with_unknown_setting(ctx, unknown_setting_error)
            return
        except SettingsFileChangedError:
            await self._respond_with_changed_file(ctx)
            return
        except SettingsValidationError as validation_error:
            await self._respond_with_rejected_change(ctx, setting_name, validation_error)
            return
        except (
            SettingsFileNotFoundError,
            InvalidSettingsFileError,
            OSError,
        ) as configuration_error:
            await self._respond_with_unusable_file(ctx, configuration_error)
            return

        # NOTE: The value itself is deliberately not repeated back, so that setting a
        # secret cannot leave a copy of it within a Discord channel.
        FORMATTED_NEW_VALUE: Final[str] = config.format_setting_value(
            config.settings.as_flat_mapping()[setting_name],
            secret=setting_metadata.secret,
        )

        logger.info("Configuration setting %r changed via the /config command.", setting_name)

        await ctx.respond(
            (
                f":white_check_mark: Set **`{setting_name}`** to "
                f"{FORMATTED_NEW_VALUE}."
                f"{_format_restart_required_warning(reload_result.restart_required_settings)}"
            ),
            ephemeral=True,
        )

    @config.command(
        name="unset",
        description="Return a single configuration setting to its default value.",
    )
    @discord.option(
        name="setting",
        description="The name of the setting to return to its default value.",
        input_type=str,
        autocomplete=autocomplete_get_settings_names,
        required=True,
        parameter_name="setting_name",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def unset(self, ctx: "TeXBotApplicationContext", setting_name: str) -> None:
        """
        Definition & callback response of the "config unset" command.

        Removes a single setting from the configuration file, returning it to its
        default value. A setting that is required cannot be removed, because the
        configuration that removing it would produce is not one TeX-Bot could load.
        """
        await ctx.defer(ephemeral=True)

        reload_result: ConfigReloadResult | None
        try:
            setting_metadata: ConfigSettingMetadata = config.setting_metadata(setting_name)
            reload_result = config.unset_setting(setting_name)
        except UnknownSettingError as unknown_setting_error:
            await self._respond_with_unknown_setting(ctx, unknown_setting_error)
            return
        except SettingsFileChangedError:
            await self._respond_with_changed_file(ctx)
            return
        except SettingsValidationError as validation_error:
            await ctx.respond(
                (
                    f":x: **`{setting_name}`** was **not** removed, because the "
                    f"configuration would no longer be valid without it. "
                    f"Nothing has been changed.\n"
                    f"```\n{validation_error}\n```"
                ),
                ephemeral=True,
            )
            return
        except (
            SettingsFileNotFoundError,
            InvalidSettingsFileError,
            OSError,
        ) as configuration_error:
            await self._respond_with_unusable_file(ctx, configuration_error)
            return

        if reload_result is None:
            await ctx.respond(
                (
                    f":information_source: **`{setting_name}`** is not set within the "
                    f"configuration file, so it is already using its default value."
                ),
                ephemeral=True,
            )
            return

        logger.info("Configuration setting %r removed via the /config command.", setting_name)

        await ctx.respond(
            (
                f":white_check_mark: Removed **`{setting_name}`**, "
                f"which has returned to its default value of "
                f"{
                    config.format_setting_value(
                        config.settings.as_flat_mapping()[setting_name],
                        secret=setting_metadata.secret,
                    )
                }."
                f"{_format_restart_required_warning(reload_result.restart_required_settings)}"
            ),
            ephemeral=True,
        )

    @staticmethod
    async def _respond_with_unknown_setting(
        ctx: "TeXBotApplicationContext", unknown_setting_error: UnknownSettingError
    ) -> None:
        """Explain that the named setting is not one that TeX-Bot has."""
        await ctx.respond(
            (
                f":x: {unknown_setting_error}\n"
                "Choose a setting from the suggestions shown as you type."
            ),
            ephemeral=True,
        )

    @staticmethod
    async def _respond_with_changed_file(ctx: "TeXBotApplicationContext") -> None:
        """Explain that the configuration file has been edited since it was loaded."""
        logger.info("A change was refused because the configuration file had been edited.")

        await ctx.respond(
            (
                ":x: The configuration file has been edited since TeX-Bot last loaded "
                "it, so nothing has been changed.\n"
                "Run `/config reload` to load those edits first, then try again."
            ),
            ephemeral=True,
        )

    @staticmethod
    async def _respond_with_rejected_change(
        ctx: "TeXBotApplicationContext",
        setting_name: str,
        validation_error: SettingsValidationError,
    ) -> None:
        """Explain that the given value was refused, & that nothing has been changed."""
        logger.warning("Change to %r rejected:\n%s", setting_name, validation_error)

        await ctx.respond(
            (
                f":x: **`{setting_name}`** was **not** changed, because that value is "
                f"not valid. Nothing has been changed.\n"
                f"```\n{validation_error}\n```"
            ),
            ephemeral=True,
        )

    @staticmethod
    async def _respond_with_unusable_file(
        ctx: "TeXBotApplicationContext", configuration_error: Exception
    ) -> None:
        """Explain that the configuration file itself could not be read or written."""
        logger.warning("Configuration file could not be used: %s", configuration_error)

        await ctx.respond(
            (
                ":x: The configuration file could not be read or written, "
                "so nothing has been changed.\n"
                f"```\n{configuration_error}\n```"
            ),
            ephemeral=True,
        )
