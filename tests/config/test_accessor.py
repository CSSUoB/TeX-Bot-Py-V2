"""Test suite for run-time access to the validated configuration."""

import datetime
from typing import TYPE_CHECKING

import pytest

from config import (
    SettingsFileNotFoundError,
    SettingsNotLoadedError,
    SettingsValidationError,
)
from config._accessor import SettingsAccessor

from .conftest import (
    CHANGED_EASTER_EGG_PROBABILITY,
    DEFAULT_EASTER_EGG_PROBABILITY,
    MINIMAL_CONFIG,
    VALID_BOT_TOKEN,
    VALID_WEBHOOK_URL,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from collections.abc import Set as AbstractSet
    from pathlib import Path
    from typing import Final

    type ConfigWriter = "Callable[[str], Path]"

__all__: "Sequence[str]" = ()


CONFIG_WITH_OPTIONAL_SETTINGS: "Final[str]" = f"""\
discord:
  bot-token: {VALID_BOT_TOKEN}
  main-guild-id: 1234567890123456789
community-group:
  full-name: Computer Science Society
  links: {{}}
  msl: {{}}
commands:
  ping:
    easter-egg-probability: 0.01
  strike:
    timeout-duration: 24h
"""


@pytest.fixture()
def loaded_accessor(config_file: "Path") -> SettingsAccessor:
    """Return an accessor that has loaded the minimal configuration."""
    settings: SettingsAccessor = SettingsAccessor()
    settings.reload(config_file)
    return settings


class TestLoading:
    """Test case for loading configuration into the accessor."""

    @staticmethod
    def test_accessing_settings_before_loading_is_refused() -> None:
        """Test that reading a setting before any configuration is loaded is refused."""
        settings: SettingsAccessor = SettingsAccessor()

        assert not settings.is_loaded

        with pytest.raises(SettingsNotLoadedError):
            _ = settings.discord.main_guild_id

    @staticmethod
    def test_nothing_loaded_has_not_been_changed_underneath() -> None:
        """
        Test that an accessor holding no configuration reports no change to the file.

        There is nothing loaded for a file to have diverged from, which is the state
        TeX-Bot is in while it is still starting up.
        """
        assert not SettingsAccessor().file_has_changed()

    @staticmethod
    def test_loading_makes_settings_available(config_file: "Path") -> None:
        """Test that settings can be read once a configuration has been loaded."""
        settings: SettingsAccessor = SettingsAccessor()

        settings.reload(config_file)

        assert settings.is_loaded
        assert settings.discord.main_guild_id == 1234567890123456789
        assert settings.file_path == config_file

    @staticmethod
    def test_defaults_are_available_for_omitted_settings(
        loaded_accessor: SettingsAccessor,
    ) -> None:
        """Test that a setting left out of the file still has its default value."""
        assert loaded_accessor.commands.strike.timeout_duration == datetime.timedelta(hours=24)
        assert loaded_accessor.community_group.membership_dependent_roles == ()

    @staticmethod
    def test_settings_are_typed(loaded_accessor: SettingsAccessor) -> None:
        """Test that settings are exposed as the types they represent."""
        assert isinstance(loaded_accessor.discord.main_guild_id, int)
        assert isinstance(loaded_accessor.commands.strike.timeout_duration, datetime.timedelta)
        assert isinstance(loaded_accessor.commands.stats.lookback_days, float)


class TestChangeDetection:
    """Test case for reporting which settings changed upon each reload."""

    @staticmethod
    def test_first_load_reports_every_setting_as_changed(config_file: "Path") -> None:
        """Test that loading a configuration for the first time reports all of it."""
        settings: SettingsAccessor = SettingsAccessor()

        assert len(settings.reload(config_file)) > 1

    @staticmethod
    def test_reloading_an_unchanged_file_reports_nothing(
        loaded_accessor: SettingsAccessor, config_file: "Path"
    ) -> None:
        """Test that reloading an untouched configuration reports no changes."""
        assert loaded_accessor.reload(config_file) == set()

    @staticmethod
    def test_a_single_change_is_reported_alone(
        write_config: "ConfigWriter",
    ) -> None:
        """Test that changing one setting reports only that setting."""
        settings: SettingsAccessor = SettingsAccessor()
        settings.reload(write_config(CONFIG_WITH_OPTIONAL_SETTINGS))

        CHANGED_SETTINGS: Final[AbstractSet[str]] = settings.reload(
            write_config(
                CONFIG_WITH_OPTIONAL_SETTINGS.replace(
                    "easter-egg-probability: 0.01", "easter-egg-probability: 0.5"
                )
            )
        )

        assert {"commands:ping:easter-egg-probability"} == CHANGED_SETTINGS
        assert settings.commands.ping.easter_egg_probability == CHANGED_EASTER_EGG_PROBABILITY

    @staticmethod
    def test_an_appearing_section_reports_the_settings_within_it(
        write_config: "ConfigWriter",
    ) -> None:
        """Test that adding an optional section reports the settings it introduces."""
        settings: SettingsAccessor = SettingsAccessor()
        settings.reload(write_config(MINIMAL_CONFIG))

        CHANGED_SETTINGS: Final[AbstractSet[str]] = settings.reload(
            write_config(
                f"{MINIMAL_CONFIG}"
                f"logging:\n"
                f"  discord-channel:\n"
                f"    webhook-url: {VALID_WEBHOOK_URL}\n"
            )
        )

        assert "logging:discord-channel:webhook-url" in CHANGED_SETTINGS
        assert settings.logging.discord_channel is not None

    @staticmethod
    def test_a_disappearing_section_reports_the_settings_it_removed(
        write_config: "ConfigWriter",
    ) -> None:
        """
        Test that removing an optional section reports the settings it took with it.

        A section that is present is expanded into the settings within it, whereas one
        that is absent collapses to a single empty value under its own name. Comparing
        one configuration against the other must therefore distinguish a key that is
        missing from a key that is present but holds nothing, or removing the section
        would appear to change nothing at all.
        """
        settings: SettingsAccessor = SettingsAccessor()
        settings.reload(
            write_config(
                f"{MINIMAL_CONFIG}"
                f"logging:\n"
                f"  discord-channel:\n"
                f"    webhook-url: {VALID_WEBHOOK_URL}\n"
            )
        )

        CHANGED_SETTINGS: Final[AbstractSet[str]] = settings.reload(
            write_config(MINIMAL_CONFIG)
        )

        assert "logging:discord-channel:webhook-url" in CHANGED_SETTINGS
        assert "logging:discord-channel" in CHANGED_SETTINGS
        assert settings.logging.discord_channel is None

    @staticmethod
    def test_a_changed_secret_is_detected(write_config: "ConfigWriter") -> None:
        """
        Test that replacing a secret value is reported as a change.

        A secret is held as an opaque object rather than as plain text, so a comparison
        that fell back to identity would report every token as unchanged & leave the
        committee member who rotated it with no warning that a restart is needed.
        """
        settings: SettingsAccessor = SettingsAccessor()
        settings.reload(write_config(MINIMAL_CONFIG))

        assert settings.reload(write_config(MINIMAL_CONFIG)) == set()

        CHANGED_SETTINGS: Final[AbstractSet[str]] = settings.reload(
            write_config(
                MINIMAL_CONFIG.replace(VALID_BOT_TOKEN, f"{VALID_BOT_TOKEN[:-4]}wxyz")
            )
        )

        assert {"discord:bot-token"} == CHANGED_SETTINGS


class TestFailedReloads:
    """Test case for what happens when a configuration cannot be loaded."""

    @staticmethod
    def test_invalid_configuration_is_rejected(
        loaded_accessor: SettingsAccessor, write_config: "ConfigWriter"
    ) -> None:
        """Test that a configuration failing validation is refused."""
        with pytest.raises(SettingsValidationError):
            loaded_accessor.reload(
                write_config(
                    f"{MINIMAL_CONFIG}commands:\n  ping:\n    easter-egg-probability: 9.9\n"
                )
            )

    @staticmethod
    def test_invalid_configuration_leaves_the_previous_one_running(
        loaded_accessor: SettingsAccessor, write_config: "ConfigWriter"
    ) -> None:
        """
        Test that a rejected configuration does not disturb the one already loaded.

        A mistake within the configuration file must not be able to take down a bot
        that is running perfectly well.
        """
        PREVIOUS_MAIN_GUILD_ID: Final[int] = loaded_accessor.discord.main_guild_id

        with pytest.raises(SettingsValidationError):
            loaded_accessor.reload(
                write_config(
                    "discord:\n"
                    "  bot-token: not-a-real-token\n"
                    "  main-guild-id: 9876543210987654321\n"
                    "community-group:\n"
                    "  links: {}\n"
                    "  msl: {}\n"
                )
            )

        assert loaded_accessor.is_loaded
        assert loaded_accessor.discord.main_guild_id == PREVIOUS_MAIN_GUILD_ID

    @staticmethod
    def test_a_missing_file_leaves_the_previous_configuration_running(
        loaded_accessor: SettingsAccessor, tmp_path: "Path"
    ) -> None:
        """Test that failing to find the file does not disturb the loaded configuration."""
        PREVIOUS_MAIN_GUILD_ID: Final[int] = loaded_accessor.discord.main_guild_id

        with pytest.raises(SettingsFileNotFoundError, match="No configuration file"):
            loaded_accessor.reload(tmp_path / "vanished.yaml")

        assert loaded_accessor.discord.main_guild_id == PREVIOUS_MAIN_GUILD_ID

    @staticmethod
    def test_validation_errors_name_the_line_responsible(
        loaded_accessor: SettingsAccessor, write_config: "ConfigWriter"
    ) -> None:
        """Test that a rejected configuration explains where the mistake is."""
        with pytest.raises(SettingsValidationError, match=r"tex-bot-deployment\.yaml:"):
            loaded_accessor.reload(
                write_config(
                    f"{MINIMAL_CONFIG}logging:\n  console:\n    log-level: NONSENSE\n"
                )
            )


class TestSnapshotIsolation:
    """Test case for the immutability of a loaded configuration."""

    @staticmethod
    def test_settings_cannot_be_modified(loaded_accessor: SettingsAccessor) -> None:
        """Test that a loaded setting cannot be overwritten in place."""
        with pytest.raises(ValueError, match="frozen"):
            loaded_accessor.discord.main_guild_id = 1  # type: ignore[misc]

    @staticmethod
    def test_a_previously_read_section_is_unaffected_by_a_reload(
        write_config: "ConfigWriter",
    ) -> None:
        """
        Test that a section read before a reload keeps the values it was read with.

        Replacing the whole snapshot, rather than mutating settings individually, is
        what stops a caller part-way through its work from seeing a mixture of the old
        and new configurations.
        """
        settings: SettingsAccessor = SettingsAccessor()
        settings.reload(write_config(CONFIG_WITH_OPTIONAL_SETTINGS))

        commands_before_reload = settings.commands

        settings.reload(
            write_config(
                CONFIG_WITH_OPTIONAL_SETTINGS.replace(
                    "easter-egg-probability: 0.01", "easter-egg-probability: 0.5"
                )
            )
        )

        assert (
            commands_before_reload.ping.easter_egg_probability
            == DEFAULT_EASTER_EGG_PROBABILITY
        )
        assert settings.commands.ping.easter_egg_probability == CHANGED_EASTER_EGG_PROBABILITY


class TestFlatMapping:
    """Test case for listing every setting by name."""

    @staticmethod
    def test_settings_are_listed_by_key_path(loaded_accessor: SettingsAccessor) -> None:
        """Test that every setting is available under its colon-separated key path."""
        FLAT_SETTINGS: Final[Mapping[str, object]] = loaded_accessor.as_flat_mapping()

        assert FLAT_SETTINGS["discord:main-guild-id"] == 1234567890123456789
        assert (
            FLAT_SETTINGS["commands:ping:easter-egg-probability"]
            == DEFAULT_EASTER_EGG_PROBABILITY
        )

    @staticmethod
    def test_secrets_are_not_revealed_by_listing_settings(
        loaded_accessor: SettingsAccessor,
    ) -> None:
        """Test that listing every setting does not expose a secret value."""
        assert VALID_BOT_TOKEN not in repr(loaded_accessor.as_flat_mapping())

    @staticmethod
    def test_listing_settings_before_loading_is_refused() -> None:
        """Test that listing settings before any are loaded is refused."""
        with pytest.raises(SettingsNotLoadedError):
            SettingsAccessor().as_flat_mapping()


class TestSectionAccessors:
    """Test case for reaching each section of the configuration."""

    @staticmethod
    def test_every_section_is_reachable(loaded_accessor: SettingsAccessor) -> None:
        """Test that each top-level section of the configuration can be read."""
        assert loaded_accessor.logging.console.log_level == "INFO"
        assert loaded_accessor.discord.main_guild_id == 1234567890123456789
        assert loaded_accessor.community_group.links.purchase_membership is None
        assert (
            loaded_accessor.commands.ping.easter_egg_probability
            == DEFAULT_EASTER_EGG_PROBABILITY
        )
        assert loaded_accessor.reminders.send_get_roles_reminders.enabled is True
        assert loaded_accessor.auto_add_committee_to_threads is True

    @staticmethod
    def test_the_underlying_document_is_reachable(
        loaded_accessor: SettingsAccessor, config_file: "Path"
    ) -> None:
        """
        Test that the document the configuration was parsed from is available.

        Rewriting an individual setting needs the document, rather than the validated
        values taken from it, so that comments & formatting are retained.
        """
        assert loaded_accessor.document.file_path == config_file
        assert "discord" in loaded_accessor.document.raw
