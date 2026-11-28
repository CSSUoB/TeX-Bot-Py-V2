"""
Contains settings values and import & setup functions.

Settings values are loaded from the `tex-bot-deployment.yaml` deployment configuration
file, validated against the schema declared within `config._schema`. These values
configure the functionality of TeX-Bot at run-time, and can be reloaded without
restarting TeX-Bot, except for those settings that require a restart.
"""

import importlib
import logging
from typing import TYPE_CHECKING, NamedTuple

from pydantic import TypeAdapter, ValidationError

from exceptions import (
    ImproperlyConfiguredError,
    InvalidSettingsFileError,
    SettingsFileChangedError,
    SettingsFileNotFoundError,
    SettingsNotLoadedError,
    SettingsValidationError,
    UnknownSettingError,
)

from ._accessor import SettingsAccessor
from ._document import SettingsDocument, get_settings_file_path
from ._editor import (
    SETTING_NAME_SEPARATOR,
    documented_setting_names,
    format_file_difference,
    format_setting_value,
    parse_setting_value,
    setting_metadata,
    validated_document_with_setting_removed,
    validated_document_with_setting_set,
)
from ._logging import (
    apply_logging_settings,
    relay_start_up_error_to_discord_log_channel,
    set_discord_log_channel_identity,
)
from ._messages import MessagesAccessor
from ._schema import ConfigSettingMetadata, DiscordWebhookURL, get_settings_metadata

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from pathlib import Path
    from typing import Final


__all__: Sequence[str] = (
    "SETTING_NAME_SEPARATOR",
    "ConfigReloadResult",
    "ConfigSettingMetadata",
    "InvalidSettingsFileError",
    "SettingsDocument",
    "SettingsFileChangedError",
    "SettingsFileNotFoundError",
    "SettingsNotLoadedError",
    "SettingsValidationError",
    "UnknownSettingError",
    "documented_setting_names",
    "format_file_difference",
    "format_setting_value",
    "get_settings_file_path",
    "get_settings_metadata",
    "messages",
    "reload_settings",
    "run_setup",
    "set_discord_log_channel_identity",
    "set_setting",
    "setting_metadata",
    "settings",
    "unset_setting",
)


logger: Final[Logger] = logging.getLogger("TeX-Bot")

settings: Final[SettingsAccessor] = SettingsAccessor()

messages: Final[MessagesAccessor] = MessagesAccessor()


class ConfigReloadResult(NamedTuple):
    """The outcome of reloading the deployment configuration file."""

    changed_settings: AbstractSet[str]
    restart_required_settings: AbstractSet[str]


def reload_settings(file_path: Path | None = None) -> ConfigReloadResult:
    """
    Reload the deployment configuration file, applying any settings that have changed.

    Returns the settings key paths whose values have changed, along with the subset of
    those that cannot take effect until TeX-Bot is restarted.

    The configuration file is located afresh unless one is given explicitly. A change
    written by `set_setting()` or `unset_setting()` names the file it was written into,
    so that the change is always read back out of the file it was made to, rather than
    out of whichever file would be located now.

    The currently loaded configuration is left untouched if the file cannot be read or
    contains invalid settings.
    """
    CHANGED_SETTINGS: Final[AbstractSet[str]] = settings.reload(file_path)

    if any(changed_setting.startswith("logging:") for changed_setting in CHANGED_SETTINGS):
        apply_logging_settings(settings.logging)

    return ConfigReloadResult(
        changed_settings=CHANGED_SETTINGS,
        # NOTE: Only a setting whose new value differs from the one TeX-Bot started with
        # needs a restart. Changing one back to its start-up value needs no restart.
        restart_required_settings=frozenset(
            CHANGED_SETTINGS & settings.values_awaiting_restart.keys()
        ),
    )


def _loaded_document() -> SettingsDocument | None:
    """Return the configuration document currently loaded, if any configuration has been."""
    return settings.document if settings.is_loaded else None


def set_setting(setting_name: str, raw_value: str) -> ConfigReloadResult:
    """
    Change a single setting within the configuration file, then apply the change.

    The new value is validated before the file is written, so a value that would be
    rejected leaves both the file & the running configuration exactly as they were.

    Changing a file that has been edited by hand since it was last loaded is refused,
    so that a change is only ever made against the configuration TeX-Bot is running.

    Returns the settings that changed as a result, along with the subset of those that
    cannot take effect until TeX-Bot is restarted.
    """
    UPDATED_DOCUMENT: Final[SettingsDocument] = validated_document_with_setting_set(
        setting_name, parse_setting_value(setting_name, raw_value), _loaded_document()
    )

    UPDATED_DOCUMENT.write()

    return reload_settings(UPDATED_DOCUMENT.file_path)


def unset_setting(setting_name: str) -> ConfigReloadResult | None:
    """
    Remove a single setting from the configuration file, then apply its removal.

    The setting returns to its default value. `None` is returned where the setting was
    not written within the file to begin with, so nothing needed to be removed.

    Removing a setting that is required leaves the file untouched, because the
    configuration that removing it would produce is not valid. Removing a setting from a
    file that has been edited by hand since it was last loaded is likewise refused.

    Removing a setting that an optional section cannot be used without (such as
    `logging:discord-channel:webhook-url`) removes the whole of that section with it.
    """
    UPDATED_DOCUMENT: Final[SettingsDocument | None] = validated_document_with_setting_removed(
        setting_name, _loaded_document()
    )

    if UPDATED_DOCUMENT is None:
        return None

    UPDATED_DOCUMENT.write()

    return reload_settings(UPDATED_DOCUMENT.file_path)


def _webhook_url_written_within_file() -> str | None:
    """
    Return the Discord log channel webhook URL written within the configuration file.

    Read from the file directly, rather than from the loaded settings, for use when
    the configuration as a whole is not valid. `None` is returned where the file
    cannot be read, or holds no webhook URL that is valid on its own.
    """
    try:
        raw_settings: object = SettingsDocument.load().raw
    except SettingsFileNotFoundError, InvalidSettingsFileError, OSError:
        return None

    key: str
    for key in ("logging", "discord-channel", "webhook-url"):
        if not isinstance(raw_settings, dict):
            return None

        raw_settings = raw_settings.get(key)

    try:
        return str(TypeAdapter(DiscordWebhookURL).validate_python(raw_settings))
    except ValidationError:
        return None


def run_setup() -> None:
    """
    Execute the setup functions required before TeX-Bot can be run.

    An error in the configuration that stops TeX-Bot from starting up is also sent to
    the Discord log channel, where one can be found, so that it is seen by whoever
    watches that channel rather than only by whoever can read the console.
    """
    settings_validation_error: SettingsValidationError
    try:
        reload_settings()
    except SettingsValidationError as settings_validation_error:
        UNVALIDATED_WEBHOOK_URL: Final[str | None] = _webhook_url_written_within_file()
        if UNVALIDATED_WEBHOOK_URL is not None:
            relay_start_up_error_to_discord_log_channel(
                settings_validation_error, UNVALIDATED_WEBHOOK_URL
            )
        raise

    messages_error: ImproperlyConfiguredError
    try:
        messages.reload()
    except ImproperlyConfiguredError as messages_error:
        if settings.logging.discord_channel is not None:
            relay_start_up_error_to_discord_log_channel(
                messages_error, str(settings.logging.discord_channel.webhook_url)
            )
        raise

    logger.debug("Begin database setup")

    importlib.import_module("db")
    importlib.import_module("django.core.management").call_command("migrate")

    logger.debug("Database setup completed")
