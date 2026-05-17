"""
Contains settings values and setup functions.

Settings values are imported from the tex-bot-deployment.yaml file.
These values are used to configure the functionality of the bot at run-time.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logging import Logger
    from typing import ClassVar, Final

    from strictyaml import YAML


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")


class SettingsAccessor:
    """
    Settings class that provides access to the settings values.

    Settings values can be accessed via key (like a dictionary) or via class attributes.
    """

    _settings: "ClassVar[dict[str, object]]" = {}
    _most_recent_yaml: "ClassVar[YAML | None]" = None

    @classmethod
    def _get_invalid_settings_key_message(cls, item: str) -> str:
        """Return the message to state that the given settings key is invalid."""
        return f"{item!r} is not a valid settings key."

    @classmethod
    async def restore_default(cls, config_setting_name: str) -> None:
        """
        Set the specified setting to its default value.

        If the setting does not have a default, it will be removed.
        """
        return

    @classmethod
    async def set_setting_value(cls, config_setting_name: str, value: object) -> None:
        """
        Set the specified setting to the given value.

        If the setting does not exist, it will be created.
        """
        return
