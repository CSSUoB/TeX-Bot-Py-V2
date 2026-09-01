"""Test suite for reloading configuration through the config package's public surface."""

import logging
from typing import TYPE_CHECKING

import pytest

import config
from config import SettingsValidationError
from config._accessor import SettingsAccessor

from .conftest import MINIMAL_CONFIG, VALID_BOT_TOKEN

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path
    from typing import Final

    from config import ConfigReloadResult

    type ConfigWriter = "Callable[[str], Path]"

__all__: "Sequence[str]" = ()


CONFIG_WITH_TASK_SETTINGS: "Final[str]" = f"""\
discord:
  bot-token: {VALID_BOT_TOKEN}
  main-guild-id: 1234567890123456789
community-group:
  links: {{}}
  msl: {{}}
logging:
  console:
    log-level: INFO
reminders:
  send-get-roles-reminders:
    enabled: true
    interval: 6h
    delay: 1d16h
"""


@pytest.fixture(autouse=True)
def _unloaded_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Replace the shared settings accessor with one holding no configuration.

    The accessor is a module-level singleton, so without this each test would begin
    holding whatever the previous test had loaded, and would report changes relative
    to it. Reloading is defined in terms of what changed, so that would make the
    results depend upon the order the tests happened to run in.
    """
    monkeypatch.setattr(config, "settings", SettingsAccessor())


@pytest.fixture()
def configured(
    write_config: "ConfigWriter", monkeypatch: pytest.MonkeyPatch
) -> "Callable[[str], ConfigReloadResult]":
    """
    Return a callable writing the given configuration & reloading it.

    Reloading through the package's public surface reads whichever file the
    `TEX_BOT_CONFIG_PATH` environment variable names, so it is pointed at a temporary
    file for the duration of each test.
    """

    def _configure(raw_yaml: str) -> "ConfigReloadResult":
        monkeypatch.setenv("TEX_BOT_CONFIG_PATH", str(write_config(raw_yaml)))
        return config.reload_settings()

    return _configure


class TestReloadResult:
    """Test case for what a reload reports back to its caller."""

    @staticmethod
    def test_reloading_an_unchanged_configuration_reports_nothing(
        configured: "Callable[[str], ConfigReloadResult]",
    ) -> None:
        """Test that reloading without editing the file reports no changes."""
        configured(CONFIG_WITH_TASK_SETTINGS)

        assert configured(CONFIG_WITH_TASK_SETTINGS).changed_settings == set()

    @staticmethod
    def test_a_changed_setting_is_reported(
        configured: "Callable[[str], ConfigReloadResult]",
    ) -> None:
        """Test that editing one setting reports exactly that setting."""
        configured(CONFIG_WITH_TASK_SETTINGS)

        RESULT: Final[ConfigReloadResult] = configured(
            CONFIG_WITH_TASK_SETTINGS.replace("log-level: INFO", "log-level: DEBUG")
        )

        assert RESULT.changed_settings == {"logging:console:log-level"}

    @staticmethod
    def test_an_invalid_configuration_is_rejected(
        configured: "Callable[[str], ConfigReloadResult]",
    ) -> None:
        """Test that a configuration failing validation is refused."""
        configured(CONFIG_WITH_TASK_SETTINGS)

        with pytest.raises(SettingsValidationError):
            configured(
                CONFIG_WITH_TASK_SETTINGS.replace("log-level: INFO", "log-level: NONSENSE")
            )

    @staticmethod
    def test_an_invalid_configuration_leaves_the_previous_one_running(
        configured: "Callable[[str], ConfigReloadResult]",
    ) -> None:
        """Test that a rejected reload does not disturb the running configuration."""
        configured(CONFIG_WITH_TASK_SETTINGS)
        PREVIOUS_LOG_LEVEL: Final[object] = config.settings.logging.console.log_level

        with pytest.raises(SettingsValidationError):
            configured(
                CONFIG_WITH_TASK_SETTINGS.replace("log-level: INFO", "log-level: NONSENSE")
            )

        assert config.settings.logging.console.log_level == PREVIOUS_LOG_LEVEL


class TestRestartRequiredClassification:
    """Test case for identifying which changes cannot take effect until a restart."""

    @staticmethod
    def test_a_live_setting_is_not_reported_as_needing_a_restart(
        configured: "Callable[[str], ConfigReloadResult]",
    ) -> None:
        """Test that a setting read at the point of use needs no restart."""
        configured(CONFIG_WITH_TASK_SETTINGS)

        RESULT: Final[ConfigReloadResult] = configured(
            CONFIG_WITH_TASK_SETTINGS.replace("log-level: INFO", "log-level: DEBUG")
        )

        assert RESULT.restart_required_settings == set()

    @staticmethod
    @pytest.mark.parametrize(
        ("original", "replacement", "expected_setting"),
        (
            (
                "main-guild-id: 1234567890123456789",
                "main-guild-id: 9876543210987654321",
                "discord:main-guild-id",
            ),
            (
                "interval: 6h",
                "interval: 30m",
                "reminders:send-get-roles-reminders:interval",
            ),
            (
                "enabled: true",
                "enabled: false",
                "reminders:send-get-roles-reminders:enabled",
            ),
        ),
    )
    def test_a_setting_fixed_at_start_up_is_reported_as_needing_a_restart(
        configured: "Callable[[str], ConfigReloadResult]",
        original: str,
        replacement: str,
        expected_setting: str,
    ) -> None:
        """Test that a setting which cannot be applied while running is flagged."""
        configured(CONFIG_WITH_TASK_SETTINGS)

        RESULT: Final[ConfigReloadResult] = configured(
            CONFIG_WITH_TASK_SETTINGS.replace(original, replacement)
        )

        assert RESULT.restart_required_settings == {expected_setting}

    @staticmethod
    def test_a_reminder_delay_does_not_require_a_restart(
        configured: "Callable[[str], ConfigReloadResult]",
    ) -> None:
        """
        Test that changing how long to wait before a reminder needs no restart.

        Unlike the interval of the task that sends them, a delay is read from the
        settings accessor at the moment it is used.
        """
        configured(CONFIG_WITH_TASK_SETTINGS)

        RESULT: Final[ConfigReloadResult] = configured(
            CONFIG_WITH_TASK_SETTINGS.replace("delay: 1d16h", "delay: 2d")
        )

        assert RESULT.changed_settings == {"reminders:send-get-roles-reminders:delay"}
        assert RESULT.restart_required_settings == set()

    @staticmethod
    def test_settings_needing_a_restart_are_a_subset_of_those_that_changed(
        configured: "Callable[[str], ConfigReloadResult]",
    ) -> None:
        """Test that nothing is reported as needing a restart unless it actually changed."""
        RESULT: Final[ConfigReloadResult] = configured(CONFIG_WITH_TASK_SETTINGS)

        assert RESULT.restart_required_settings <= RESULT.changed_settings


class TestLoggingApplication:
    """Test case for applying logging settings as part of a reload."""

    @staticmethod
    def test_changing_the_console_log_level_takes_effect(
        configured: "Callable[[str], ConfigReloadResult]",
    ) -> None:
        """Test that a new console log level is applied to the logger immediately."""
        configured(CONFIG_WITH_TASK_SETTINGS)

        configured(CONFIG_WITH_TASK_SETTINGS.replace("log-level: INFO", "log-level: DEBUG"))

        assert logging.getLogger("TeX-Bot").level == logging.DEBUG

    @staticmethod
    def test_reloading_repeatedly_does_not_accumulate_handlers(
        configured: "Callable[[str], ConfigReloadResult]",
    ) -> None:
        """
        Test that reloading many times does not add a logging handler each time.

        Accumulating handlers would cause every log record to be emitted repeatedly.
        """
        configured(CONFIG_WITH_TASK_SETTINGS)
        HANDLER_COUNT_AFTER_FIRST_LOAD: Final[int] = len(logging.getLogger("TeX-Bot").handlers)

        for log_level in ("DEBUG", "WARNING", "ERROR", "INFO"):
            configured(
                CONFIG_WITH_TASK_SETTINGS.replace("log-level: INFO", f"log-level: {log_level}")
            )

        assert len(logging.getLogger("TeX-Bot").handlers) == HANDLER_COUNT_AFTER_FIRST_LOAD


def test_minimal_configuration_reloads(
    configured: "Callable[[str], ConfigReloadResult]",
) -> None:
    """Test that a configuration holding only the required settings can be reloaded."""
    assert configured(MINIMAL_CONFIG).changed_settings
