"""Test suite for the "/config" command group."""

import asyncio
from typing import TYPE_CHECKING, cast, override

import pytest

import config
from config._accessor import SettingsAccessor
from config._document import SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME

from .conftest import MINIMAL_CONFIG, VALID_BOT_TOKEN

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from pathlib import Path
    from typing import Final

    from cogs.config import ConfigCommandsCog
    from utils import TeXBot

    type ConfigReloadRunner = "Callable[[str | None], Sequence[str]]"

__all__: Sequence[str] = ()


class _RecordingApplicationContext:
    """A stand-in for the Discord context that a slash command is invoked with."""

    @override
    def __init__(self) -> None:
        """Initialise a context that has been responded to with nothing so far."""
        self.responses: list[str] = []

    async def defer(self, *, ephemeral: bool = False) -> None:
        """Record that the command asked for more time to respond."""

    async def respond(self, message: str, *, ephemeral: bool = False) -> None:  # noqa: ARG002
        """Record a response sent back to the committee member that ran the command."""
        self.responses.append(message)


@pytest.fixture(scope="module")
def config_commands_cog(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[type[ConfigCommandsCog]]:
    """
    Return the cog class defining the `/config` command group.

    Importing any cog loads every other one alongside it, several of which read the
    configuration as they are imported, so a valid configuration must already be loaded
    before the import can succeed at all.
    """
    with pytest.MonkeyPatch.context() as module_monkeypatch:
        CONFIG_FILE_PATH: Final[Path] = (
            tmp_path_factory.mktemp("config-command") / "tex-bot-deployment.yaml"
        )
        CONFIG_FILE_PATH.write_text(MINIMAL_CONFIG, encoding="utf-8")
        module_monkeypatch.setenv(
            SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME, str(CONFIG_FILE_PATH)
        )
        config.reload_settings()

        from cogs.config import ConfigCommandsCog  # noqa: PLC0415

        yield ConfigCommandsCog


@pytest.fixture()
def run_config_reload(
    config_commands_cog: type[ConfigCommandsCog],
    write_config: Callable[[str], Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> ConfigReloadRunner:
    """
    Return a callable running the `/config reload` command against the given file.

    Passing `None` in place of a configuration runs the command with no configuration
    file present at all. Each test begins from an accessor holding no configuration, so
    that what the command reports does not depend upon what the previous test loaded.
    """
    monkeypatch.setattr(config, "settings", SettingsAccessor())

    # NOTE: The reload command never reaches for the running bot, so it does not need
    # a connection to Discord in order to be exercised.
    cog: ConfigCommandsCog = config_commands_cog(bot=cast("TeXBot", None))

    def _run_config_reload(raw_yaml: str | None) -> Sequence[str]:
        monkeypatch.setenv(
            SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME,
            str(
                write_config(raw_yaml)
                if raw_yaml is not None
                else tmp_path / "no-such-file.yaml"
            ),
        )

        context: _RecordingApplicationContext = _RecordingApplicationContext()
        asyncio.run(config_commands_cog.reload.callback(cog, context))

        return context.responses

    return _run_config_reload


class TestSuccessfulReloads:
    """Test case for reloading a configuration that can be applied."""

    @staticmethod
    def test_the_settings_that_changed_are_reported(
        run_config_reload: ConfigReloadRunner,
    ) -> None:
        """Test that a successful reload names the settings it applied."""
        run_config_reload(MINIMAL_CONFIG)

        RESPONSES: Final[Sequence[str]] = run_config_reload(
            f"{MINIMAL_CONFIG}logging:\n  console:\n    log-level: DEBUG\n"
        )

        assert len(RESPONSES) == 1
        assert "Reloaded the configuration file" in RESPONSES[0]
        assert "`logging:console:log-level`" in RESPONSES[0]

    @staticmethod
    def test_an_unchanged_configuration_is_reported(
        run_config_reload: ConfigReloadRunner,
    ) -> None:
        """Test that reloading without editing the file says so, rather than nothing."""
        run_config_reload(MINIMAL_CONFIG)

        RESPONSES: Final[Sequence[str]] = run_config_reload(MINIMAL_CONFIG)

        assert len(RESPONSES) == 1
        assert "has not changed" in RESPONSES[0]

    @staticmethod
    def test_a_very_long_list_of_changes_is_truncated(
        run_config_reload: ConfigReloadRunner,
    ) -> None:
        """
        Test that reporting a great many changes does not produce an endless message.

        The very first reload reports every setting as changed, which is far more than
        can be listed within a single Discord message.
        """
        from cogs.config import MAXIMUM_LISTED_SETTINGS  # noqa: PLC0415

        RESPONSES: Final[Sequence[str]] = run_config_reload(MINIMAL_CONFIG)

        CHANGED_SETTINGS_LIST: Final[str] = RESPONSES[0].split(":warning:")[0]

        assert "- _...and " in CHANGED_SETTINGS_LIST
        assert CHANGED_SETTINGS_LIST.count("\n- `") == MAXIMUM_LISTED_SETTINGS


class TestRestartRequiredWarning:
    """Test case for warning that a change cannot take effect until a restart."""

    @staticmethod
    def test_a_setting_fixed_at_start_up_is_called_out(
        run_config_reload: ConfigReloadRunner,
    ) -> None:
        """Test that changing a setting which needs a restart says so explicitly."""
        run_config_reload(MINIMAL_CONFIG)

        RESPONSES: Final[Sequence[str]] = run_config_reload(
            MINIMAL_CONFIG.replace("1234567890123456789", "9876543210987654321")
        )

        assert "must be restarted" in RESPONSES[0]
        assert "`discord:main-guild-id`" in RESPONSES[0]

    @staticmethod
    def test_a_setting_applied_immediately_is_not_called_out(
        run_config_reload: ConfigReloadRunner,
    ) -> None:
        """Test that a change taking effect at once does not ask for a restart."""
        run_config_reload(MINIMAL_CONFIG)

        RESPONSES: Final[Sequence[str]] = run_config_reload(
            f"{MINIMAL_CONFIG}logging:\n  console:\n    log-level: DEBUG\n"
        )

        assert "must be restarted" not in RESPONSES[0]


class TestSettingsAwaitingRestart:
    """Test case for showing a setting whose new value is waiting for a restart."""

    @staticmethod
    def test_setting_a_value_reports_the_new_value(
        run_config_reload: ConfigReloadRunner,
        config_commands_cog: type[ConfigCommandsCog],
    ) -> None:
        """
        Test that changing a setting which needs a restart repeats back its new value.

        TeX-Bot keeps running with the old value until it restarts, so repeating back
        the value it is running would look as though the change had been ignored.
        """
        run_config_reload(MINIMAL_CONFIG)

        context: _RecordingApplicationContext = _RecordingApplicationContext()
        asyncio.run(
            config_commands_cog.set.callback(
                config_commands_cog(bot=cast("TeXBot", None)),
                context,
                "discord:main-guild-id",
                "9876543210987654321",
            )
        )

        assert "to `9876543210987654321`" in context.responses[0]
        assert "must be restarted" in context.responses[0]

    @staticmethod
    def test_the_value_awaiting_a_restart_is_shown(
        run_config_reload: ConfigReloadRunner,
        config_commands_cog: type[ConfigCommandsCog],
    ) -> None:
        """Test that viewing a setting shows both the running value & the one to come."""
        run_config_reload(MINIMAL_CONFIG)
        run_config_reload(MINIMAL_CONFIG.replace("1234567890123456789", "9876543210987654321"))

        context: _RecordingApplicationContext = _RecordingApplicationContext()
        asyncio.run(
            config_commands_cog.get.callback(
                config_commands_cog(bot=cast("TeXBot", None)),
                context,
                "discord:main-guild-id",
            )
        )

        assert "`1234567890123456789`" in context.responses[0]
        assert (
            "The configuration file changes this to `9876543210987654321`, "
            "which will not take effect until TeX-Bot is restarted."
        ) in context.responses[0]

    @staticmethod
    def test_a_value_awaiting_a_restart_is_not_mistaken_for_an_edit_by_hand(
        run_config_reload: ConfigReloadRunner,
        config_commands_cog: type[ConfigCommandsCog],
        write_config: Callable[[str], Path],
    ) -> None:
        """
        Test that a reload is not suggested to apply a value only a restart can apply.

        A different setting is edited by hand, so the file no longer matches what was
        loaded, but the setting being viewed was not touched by that edit.
        """
        CHANGED_CONFIG: Final[str] = MINIMAL_CONFIG.replace(
            "1234567890123456789", "9876543210987654321"
        )
        run_config_reload(MINIMAL_CONFIG)
        run_config_reload(CHANGED_CONFIG)
        write_config(f"{CHANGED_CONFIG}logging:\n  console:\n    log-level: DEBUG\n")

        context: _RecordingApplicationContext = _RecordingApplicationContext()
        asyncio.run(
            config_commands_cog.get.callback(
                config_commands_cog(bot=cast("TeXBot", None)),
                context,
                "discord:main-guild-id",
            )
        )

        assert "though not this setting" in context.responses[0]
        assert "will not take effect until TeX-Bot is restarted" in context.responses[0]

    @staticmethod
    def test_a_start_up_value_is_not_called_the_default(
        run_config_reload: ConfigReloadRunner,
        config_commands_cog: type[ConfigCommandsCog],
    ) -> None:
        """Test that removing a setting needing a restart does not relabel its old value."""
        run_config_reload(f"{MINIMAL_CONFIG}community-group:\n  short-name: CSS\n")
        run_config_reload(MINIMAL_CONFIG)

        context: _RecordingApplicationContext = _RecordingApplicationContext()
        asyncio.run(
            config_commands_cog.get.callback(
                config_commands_cog(bot=cast("TeXBot", None)),
                context,
                "community-group:short-name",
            )
        )

        assert "`CSS`" in context.responses[0]
        assert "(default" not in context.responses[0]
        assert "The configuration file changes this to" in context.responses[0]


class TestRejectedReloads:
    """Test case for reporting a configuration that could not be loaded."""

    @staticmethod
    def test_invalid_settings_are_reported_without_being_applied(
        run_config_reload: ConfigReloadRunner,
    ) -> None:
        """Test that a configuration failing validation is refused & explained."""
        run_config_reload(MINIMAL_CONFIG)

        RESPONSES: Final[Sequence[str]] = run_config_reload(
            f"{MINIMAL_CONFIG}logging:\n  console:\n    log-level: NONSENSE\n"
        )

        assert "was **not** loaded" in RESPONSES[0]
        assert "invalid settings" in RESPONSES[0]
        assert config.settings.logging.console.log_level == "INFO"

    @staticmethod
    def test_a_rejected_secret_is_not_echoed_back(
        run_config_reload: ConfigReloadRunner,
    ) -> None:
        """Test that an invalid token is not quoted back into a Discord channel."""
        INVALID_TOKEN: Final[str] = "NOT-A-REAL-TOKEN-BUT-STILL-SECRET"  # noqa: S105

        run_config_reload(MINIMAL_CONFIG)

        RESPONSES: Final[Sequence[str]] = run_config_reload(
            MINIMAL_CONFIG.replace(VALID_BOT_TOKEN, INVALID_TOKEN)
        )

        assert "was **not** loaded" in RESPONSES[0]
        assert INVALID_TOKEN not in RESPONSES[0]

    @staticmethod
    def test_a_configuration_holding_many_errors_still_fits_within_one_message(
        run_config_reload: ConfigReloadRunner,
    ) -> None:
        """
        Test that a great many validation failures are shortened rather than refused.

        Discord rejects a message beyond its length limit in its entirety, so a response
        that was not shortened would leave the committee member with no explanation at
        all, at exactly the moment one is most needed.
        """
        from cogs.config import MAXIMUM_MESSAGE_LENGTH, TRUNCATION_NOTICE  # noqa: PLC0415

        UNKNOWN_SETTINGS: Final[str] = "".join(
            f"unknown-setting-{unknown_setting_number}: {unknown_setting_number}\n"
            for unknown_setting_number in range(100)
        )

        run_config_reload(MINIMAL_CONFIG)

        RESPONSES: Final[Sequence[str]] = run_config_reload(
            f"{MINIMAL_CONFIG}{UNKNOWN_SETTINGS}"
        )

        assert "was **not** loaded" in RESPONSES[0]
        assert len(RESPONSES[0]) <= MAXIMUM_MESSAGE_LENGTH
        assert RESPONSES[0].endswith("```")
        assert TRUNCATION_NOTICE in RESPONSES[0]

    @staticmethod
    def test_a_missing_configuration_file_is_reported(
        run_config_reload: ConfigReloadRunner,
    ) -> None:
        """
        Test that running the command with no configuration file is reported clearly.

        Failing to find the file does not raise an operating-system error, so catching
        one is not enough to keep this from surfacing as an unhandled exception.
        """
        run_config_reload(MINIMAL_CONFIG)

        RESPONSES: Final[Sequence[str]] = run_config_reload(None)

        assert len(RESPONSES) == 1
        assert "could not be read" in RESPONSES[0]

    @staticmethod
    @pytest.mark.parametrize(
        "raw_yaml", ("discord:\n  bot-token: [unclosed\n", "", "just-a-string\n")
    )
    def test_an_unreadable_configuration_file_is_reported(
        run_config_reload: ConfigReloadRunner, raw_yaml: str
    ) -> None:
        """
        Test that a file that cannot be parsed at all is reported clearly.

        Nor does failing to parse the file raise an operating-system error, so this too
        would otherwise surface as an unhandled exception rather than as an explanation.
        """
        run_config_reload(MINIMAL_CONFIG)

        RESPONSES: Final[Sequence[str]] = run_config_reload(raw_yaml)

        assert len(RESPONSES) == 1
        assert "could not be read" in RESPONSES[0]
