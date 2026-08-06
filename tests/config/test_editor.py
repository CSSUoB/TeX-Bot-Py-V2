"""Test suite for changing individual settings within the configuration file."""

import datetime
from typing import TYPE_CHECKING

import pytest

import config
from config import (
    SettingsFileChangedError,
    SettingsValidationError,
    UnknownSettingError,
)
from config._accessor import SettingsAccessor
from config._document import SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME, SettingsDocument
from config._editor import format_setting_value, parse_setting_value

from .conftest import (
    CHANGED_EASTER_EGG_PROBABILITY,
    DEFAULT_EASTER_EGG_PROBABILITY,
    MINIMAL_CONFIG,
    VALID_BOT_TOKEN,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path
    from typing import Final

    from config import ConfigReloadResult

    type ConfigWriter = "Callable[[str], Path]"

__all__: "Sequence[str]" = ()


COMMENTED_CONFIG: "Final[str]" = f"""\
# A leading comment about the whole file.
discord:
  # A comment about the bot token.
  bot-token: {VALID_BOT_TOKEN}
  main-guild-id: 1234567890123456789
community-group:
  full-name: Computer Science Society
  links: {{}}
  msl: {{}}
commands:
  ping:
    easter-egg-probability: 0.01
"""


@pytest.fixture()
def configured(
    write_config: "ConfigWriter", monkeypatch: pytest.MonkeyPatch
) -> "Callable[[str], Path]":
    """
    Return a callable writing the given configuration & loading it.

    Changing a setting reads & rewrites whichever file the `TEX_BOT_CONFIG_PATH`
    environment variable names, so it is pointed at a temporary file for each test.
    """
    monkeypatch.setattr(config, "settings", SettingsAccessor())

    def _configure(raw_yaml: str) -> "Path":
        CONFIG_FILE_PATH: Final[Path] = write_config(raw_yaml)
        monkeypatch.setenv(SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME, str(CONFIG_FILE_PATH))
        config.reload_settings()
        return CONFIG_FILE_PATH

    return _configure


class TestParsingValues:
    """Test case for reading the value that a committee member typed."""

    @staticmethod
    @pytest.mark.parametrize(
        ("raw_value", "expected_value"),
        (
            ("true", True),
            ("false", False),
            ("0.5", 0.5),
            ("30", 30),
            ("1h30m", "1h30m"),
            ("DM", "DM"),
            ("[Committee, Member]", ["Committee", "Member"]),
        ),
    )
    def test_a_value_is_read_as_it_would_be_written(
        raw_value: str, expected_value: object
    ) -> None:
        """Test that a value is read exactly as the same text within the file would be."""
        assert (
            parse_setting_value("commands:strike:timeout-duration", raw_value)
            == expected_value
        )

    @staticmethod
    @pytest.mark.parametrize(
        "setting_name",
        # NOTE: One setting declared to hold text & one that is not, because each is
        # read by a separate path through the parser.
        ("community-group:full-name", "commands:strike:timeout-duration"),
    )
    def test_a_value_holding_a_colon_is_kept_as_text(setting_name: str) -> None:
        """
        Test that text containing a colon is not read as a section of its own.

        `Computer Science: Society` is a perfectly ordinary name, but is also how a
        mapping of one key to one value is written.
        """
        assert (
            parse_setting_value(setting_name, "Computer Science: Society")
            == "Computer Science: Society"
        )

    @staticmethod
    @pytest.mark.parametrize(
        "setting_name",
        (
            "commands:strike:performed-manually-warning-location",
            "commands:strike:timeout-duration",
        ),
    )
    def test_a_value_beginning_with_a_hash_is_kept_as_text(setting_name: str) -> None:
        """Test that text that would otherwise be read as a comment is kept."""
        assert parse_setting_value(setting_name, "#staff") == "#staff"

    @staticmethod
    @pytest.mark.parametrize(
        "setting_name",
        (
            "commands:strike:performed-manually-warning-location",
            "commands:strike:timeout-duration",
        ),
    )
    def test_a_value_that_is_not_valid_yaml_is_kept_as_text(setting_name: str) -> None:
        """Test that text which happens to be malformed YAML is kept as the text it is."""
        assert parse_setting_value(setting_name, '"unclosed quote') == '"unclosed quote'

    @staticmethod
    def test_every_setting_can_be_named() -> None:
        """Test that each setting that exists is offered as one that can be changed."""
        SETTINGS_NAMES: Final[Sequence[str]] = config.documented_setting_names()

        assert "commands:ping:easter-egg-probability" in SETTINGS_NAMES
        assert list(SETTINGS_NAMES) == sorted(config.get_settings_metadata())

    @staticmethod
    @pytest.mark.parametrize("raw_value", ("1234", '"1234"', "'1234'"))
    def test_a_setting_holding_text_keeps_a_value_that_looks_numeric(
        raw_value: str,
    ) -> None:
        """
        Test that a value which looks like a number stays text where text is expected.

        An MSL organisation ID is four or five digits, so somebody setting one will
        write it exactly as they see it, without quoting it as YAML would require.
        """
        assert parse_setting_value("community-group:msl:organisation-id", raw_value) == "1234"

    @staticmethod
    def test_a_setting_holding_a_sequence_is_not_mistaken_for_text() -> None:
        """Test that a list of role names is still read as a list."""
        assert parse_setting_value("commands:stats:displayed-roles", "[Committee]") == [
            "Committee"
        ]

    @staticmethod
    def test_an_unknown_setting_is_refused() -> None:
        """Test that reading a value for a setting that does not exist is refused."""
        with pytest.raises(UnknownSettingError, match="not:a:setting"):
            parse_setting_value("not:a:setting", "1")


class TestChangingSettings:
    """Test case for writing a single setting into the configuration file."""

    @staticmethod
    def test_a_changed_setting_is_applied(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that changing a setting takes effect immediately."""
        configured(COMMENTED_CONFIG)

        RESULT: Final[ConfigReloadResult] = config.set_setting(
            "commands:ping:easter-egg-probability", "0.5"
        )

        assert RESULT.changed_settings == {"commands:ping:easter-egg-probability"}
        assert (
            config.settings.commands.ping.easter_egg_probability
            == CHANGED_EASTER_EGG_PROBABILITY
        )

    @staticmethod
    def test_a_changed_setting_is_written_to_the_file(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that a changed setting survives being loaded again."""
        CONFIG_FILE_PATH: Final[Path] = configured(COMMENTED_CONFIG)

        config.set_setting("commands:ping:easter-egg-probability", "0.5")

        assert (
            SettingsDocument.load(CONFIG_FILE_PATH).raw["commands"]["ping"][
                "easter-egg-probability"
            ]
            == CHANGED_EASTER_EGG_PROBABILITY
        )

    @staticmethod
    def test_changing_a_setting_preserves_every_comment(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that rewriting the file keeps the annotations a human wrote within it."""
        CONFIG_FILE_PATH: Final[Path] = configured(COMMENTED_CONFIG)

        config.set_setting("commands:ping:easter-egg-probability", "0.5")

        NEW_FILE_CONTENTS: Final[str] = CONFIG_FILE_PATH.read_text(encoding="utf-8")

        assert "# A leading comment about the whole file." in NEW_FILE_CONTENTS
        assert "# A comment about the bot token." in NEW_FILE_CONTENTS

    @staticmethod
    def test_a_setting_within_an_absent_section_is_created(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that setting a value creates whichever sections are needed to hold it."""
        configured(MINIMAL_CONFIG)

        config.set_setting("reminders:send-get-roles-reminders:interval", "30m")

        assert config.settings.reminders.send_get_roles_reminders.interval == (
            datetime.timedelta(minutes=30)
        )

    @staticmethod
    def test_a_change_needing_a_restart_is_reported(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that changing a setting fixed at start-up says a restart is needed."""
        configured(COMMENTED_CONFIG)

        RESULT: Final[ConfigReloadResult] = config.set_setting(
            "reminders:send-get-roles-reminders:interval", "30m"
        )

        assert RESULT.restart_required_settings == {
            "reminders:send-get-roles-reminders:interval"
        }

    @staticmethod
    def test_an_unknown_setting_is_refused(configured: "Callable[[str], Path]") -> None:
        """Test that changing a setting that does not exist is refused."""
        configured(COMMENTED_CONFIG)

        with pytest.raises(UnknownSettingError):
            config.set_setting("not:a:setting", "1")


class TestRejectedChanges:
    """Test case for refusing a change that would produce an invalid configuration."""

    @staticmethod
    def test_an_invalid_value_is_rejected(configured: "Callable[[str], Path]") -> None:
        """Test that a value outside what a setting allows is refused."""
        configured(COMMENTED_CONFIG)

        with pytest.raises(SettingsValidationError):
            config.set_setting("commands:ping:easter-egg-probability", "9.9")

    @staticmethod
    def test_a_rejected_change_does_not_touch_the_file(
        configured: "Callable[[str], Path]",
    ) -> None:
        """
        Test that a refused change leaves the configuration file exactly as it was.

        The change is validated against a copy of the file, so a value that turns out to
        be invalid never reaches the file that TeX-Bot would load next.
        """
        CONFIG_FILE_PATH: Final[Path] = configured(COMMENTED_CONFIG)

        with pytest.raises(SettingsValidationError):
            config.set_setting("commands:ping:easter-egg-probability", "9.9")

        assert CONFIG_FILE_PATH.read_text(encoding="utf-8") == COMMENTED_CONFIG

    @staticmethod
    def test_a_rejected_change_leaves_the_running_configuration_alone(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that a refused change does not disturb the settings already loaded."""
        configured(COMMENTED_CONFIG)

        with pytest.raises(SettingsValidationError):
            config.set_setting("commands:ping:easter-egg-probability", "9.9")

        assert (
            config.settings.commands.ping.easter_egg_probability
            == DEFAULT_EASTER_EGG_PROBABILITY
        )

    @staticmethod
    def test_a_rejected_new_setting_is_reported_without_a_line_number(
        configured: "Callable[[str], Path]",
    ) -> None:
        """
        Test that refusing a setting absent from the file is reported, not crashed upon.

        A setting being written for the first time has no line within the file it came
        from, so there is no line number to report it against.
        """
        configured(MINIMAL_CONFIG)

        with pytest.raises(SettingsValidationError) as validation_error:
            config.set_setting("reminders:send-get-roles-reminders:interval", "0s")

        assert "reminders:send-get-roles-reminders:interval" in str(validation_error.value)


class TestChangesMadeByHand:
    """
    Test case for a change made from within Discord meeting one made by hand.

    A configuration file that has been edited since it was last loaded is refused rather
    than merged into, so that a change is only ever made against the configuration that
    TeX-Bot is actually running.
    """

    @staticmethod
    def _edit_by_hand(config_file_path: "Path", original: str, replacement: str) -> None:
        """Edit the configuration file directly, as somebody with a text editor would."""
        config_file_path.write_text(
            config_file_path.read_text(encoding="utf-8").replace(original, replacement),
            encoding="utf-8",
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("original", "replacement"),
        (
            # NOTE: An edit to the setting being changed, to a different setting, one
            # adding a setting, one removing a setting, & one changing nothing at all.
            ("easter-egg-probability: 0.01", "easter-egg-probability: 0.25"),
            ("full-name: Computer Science Society", "full-name: Edited By Hand"),
            ("community-group:\n", "auto-add-committee-to-threads: false\ncommunity-group:\n"),
            ("  full-name: Computer Science Society\n", ""),
            ("discord:\n", "# A comment added by hand.\ndiscord:\n"),
        ),
    )
    def test_a_change_is_refused_while_the_file_has_been_edited(
        configured: "Callable[[str], Path]", original: str, replacement: str
    ) -> None:
        """Test that any edit made by hand refuses a change made from within Discord."""
        CONFIG_FILE_PATH: Final[Path] = configured(COMMENTED_CONFIG)

        TestChangesMadeByHand._edit_by_hand(CONFIG_FILE_PATH, original, replacement)
        CONFIG_FILE_CONTENTS_AFTER_EDIT: Final[str] = CONFIG_FILE_PATH.read_text(
            encoding="utf-8"
        )

        with pytest.raises(SettingsFileChangedError):
            config.set_setting("commands:ping:easter-egg-probability", "0.5")

        assert CONFIG_FILE_PATH.read_text(encoding="utf-8") == CONFIG_FILE_CONTENTS_AFTER_EDIT
        assert (
            config.settings.commands.ping.easter_egg_probability
            == DEFAULT_EASTER_EGG_PROBABILITY
        )

    @staticmethod
    def test_a_removal_is_refused_while_the_file_has_been_edited(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that an edit made by hand refuses a removal too, not only a change."""
        CONFIG_FILE_PATH: Final[Path] = configured(COMMENTED_CONFIG)

        TestChangesMadeByHand._edit_by_hand(
            CONFIG_FILE_PATH,
            "full-name: Computer Science Society",
            "full-name: Edited By Hand",
        )

        with pytest.raises(SettingsFileChangedError):
            config.unset_setting("commands:ping:easter-egg-probability")

        assert config.settings.community_group.full_name == "Computer Science Society"

    @staticmethod
    def test_reloading_first_allows_the_change_to_be_made(
        configured: "Callable[[str], Path]",
    ) -> None:
        """
        Test that loading the edits made by hand is enough to allow a change again.

        This is what the refusal tells whoever ran the command to do, so it has to be
        the case that doing it lets them carry on.
        """
        CONFIG_FILE_PATH: Final[Path] = configured(COMMENTED_CONFIG)

        TestChangesMadeByHand._edit_by_hand(
            CONFIG_FILE_PATH,
            "full-name: Computer Science Society",
            "full-name: Edited By Hand",
        )

        config.reload_settings()
        config.set_setting("commands:ping:easter-egg-probability", "0.5")

        assert config.settings.community_group.full_name == "Edited By Hand"
        assert (
            config.settings.commands.ping.easter_egg_probability
            == CHANGED_EASTER_EGG_PROBABILITY
        )

    @staticmethod
    def test_a_comment_added_by_hand_is_cleared_by_reloading(
        configured: "Callable[[str], Path]",
    ) -> None:
        """
        Test that reloading clears the refusal even for an edit that changed no setting.

        Reloading replaces the document it holds as well as the settings taken from it,
        so an edit that altered only the comments no longer counts as outstanding.
        """
        CONFIG_FILE_PATH: Final[Path] = configured(COMMENTED_CONFIG)

        TestChangesMadeByHand._edit_by_hand(
            CONFIG_FILE_PATH, "discord:\n", "# A comment added by hand.\ndiscord:\n"
        )

        assert config.reload_settings().changed_settings == set()

        config.set_setting("commands:ping:easter-egg-probability", "0.5")

        assert "# A comment added by hand." in CONFIG_FILE_PATH.read_text(encoding="utf-8")

    @staticmethod
    def test_a_change_made_from_discord_does_not_refuse_the_next_one(
        configured: "Callable[[str], Path]",
    ) -> None:
        """
        Test that changing a setting does not leave the file looking edited by hand.

        Each change rewrites the file, so the check has to recognise TeX-Bot's own
        writing as its own, or no second change could ever be made.
        """
        configured(COMMENTED_CONFIG)

        config.set_setting("commands:ping:easter-egg-probability", "0.5")
        config.set_setting("community-group:full-name", "CompSoc")

        assert config.settings.community_group.full_name == "CompSoc"

    @staticmethod
    def test_an_unedited_file_is_not_reported_as_changed(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that a file nobody has touched is not mistaken for one that was edited."""
        configured(COMMENTED_CONFIG)

        assert not config.settings.file_has_changed()

    @staticmethod
    def test_differing_line_endings_are_not_mistaken_for_an_edit(
        configured: "Callable[[str], Path]",
    ) -> None:
        """
        Test that rewriting the file with other line endings does not count as an edit.

        A configuration file edited upon one operating system & used upon another is
        commonplace, & says nothing about whether its settings were changed.
        """
        CONFIG_FILE_PATH: Final[Path] = configured(COMMENTED_CONFIG)

        CONFIG_FILE_PATH.write_bytes(
            COMMENTED_CONFIG.replace("\n", "\r\n").encode(encoding="utf-8")
        )

        assert not config.settings.file_has_changed()


class TestRemovingSettings:
    """Test case for returning a single setting to its default value."""

    @staticmethod
    def test_a_removed_setting_returns_to_its_default(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that removing a setting restores the value it would otherwise have."""
        configured(COMMENTED_CONFIG)

        RESULT: Final[ConfigReloadResult | None] = config.unset_setting(
            "community-group:full-name"
        )

        assert RESULT is not None
        assert RESULT.changed_settings == {"community-group:full-name"}
        assert config.settings.community_group.full_name is None

    @staticmethod
    def test_removing_a_setting_that_is_not_set_changes_nothing(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that removing a setting absent from the file is reported as such."""
        CONFIG_FILE_PATH: Final[Path] = configured(MINIMAL_CONFIG)

        assert config.unset_setting("community-group:full-name") is None
        assert CONFIG_FILE_PATH.read_text(encoding="utf-8") == MINIMAL_CONFIG

    @staticmethod
    def test_removing_an_unknown_setting_is_refused(
        configured: "Callable[[str], Path]",
    ) -> None:
        """Test that removing a setting that does not exist is refused."""
        configured(COMMENTED_CONFIG)

        with pytest.raises(UnknownSettingError):
            config.unset_setting("not:a:setting")

    @staticmethod
    def test_removing_a_required_setting_is_refused(
        configured: "Callable[[str], Path]",
    ) -> None:
        """
        Test that a setting TeX-Bot cannot run without is not removed.

        No special knowledge of which settings are required is needed: the configuration
        that removing it would produce simply does not validate.
        """
        CONFIG_FILE_PATH: Final[Path] = configured(COMMENTED_CONFIG)

        with pytest.raises(SettingsValidationError):
            config.unset_setting("discord:bot-token")

        assert CONFIG_FILE_PATH.read_text(encoding="utf-8") == COMMENTED_CONFIG
        assert config.settings.discord.bot_token.get_secret_value() == VALID_BOT_TOKEN

    @staticmethod
    def test_a_section_left_empty_is_still_valid(
        configured: "Callable[[str], Path]",
    ) -> None:
        """
        Test that removing the last setting of a section leaves a usable file.

        A section holding nothing is kept rather than removed, because a section may be
        required to be present even when every setting within it is left at its default.
        """
        configured(COMMENTED_CONFIG)

        config.unset_setting("commands:ping:easter-egg-probability")

        assert (
            config.settings.commands.ping.easter_egg_probability
            == DEFAULT_EASTER_EGG_PROBABILITY
        )
        assert config.reload_settings().changed_settings == set()


class TestDisplayingValues:
    """Test case for rendering a setting's value into something readable."""

    @staticmethod
    @pytest.mark.parametrize(
        ("duration", "expected_display"),
        (
            (datetime.timedelta(hours=24), "`1d`"),
            (datetime.timedelta(minutes=30), "`30m`"),
            (datetime.timedelta(hours=1, minutes=30), "`1h30m`"),
            (datetime.timedelta(days=1, hours=16), "`1d16h`"),
            (datetime.timedelta(seconds=45), "`45s`"),
            (datetime.timedelta(0), "`0s`"),
        ),
    )
    def test_a_duration_is_shown_in_the_format_it_is_written_in(
        duration: datetime.timedelta, expected_display: str
    ) -> None:
        """Test that a length of time is shown the way it would be written in the file."""
        assert format_setting_value(duration, secret=False) == expected_display

    @staticmethod
    def test_a_secret_value_is_never_shown() -> None:
        """Test that displaying a secret setting does not reveal it."""
        FORMATTED_VALUE: Final[str] = format_setting_value(VALID_BOT_TOKEN, secret=True)

        assert VALID_BOT_TOKEN not in FORMATTED_VALUE

    @staticmethod
    def test_an_unset_value_is_shown_as_unset() -> None:
        """Test that a setting holding nothing says so, rather than showing nothing."""
        assert "not set" in format_setting_value(None, secret=False)

    @staticmethod
    @pytest.mark.parametrize(
        ("value", "expected_display"),
        (
            (True, "`true`"),
            (False, "`false`"),
            (("Committee", "Member"), "`Committee`, `Member`"),
            (0.01, "`0.01`"),
        ),
    )
    def test_a_value_is_shown_as_it_is_written(value: object, expected_display: str) -> None:
        """Test that each kind of value is shown the way it appears within the file."""
        assert format_setting_value(value, secret=False) == expected_display
