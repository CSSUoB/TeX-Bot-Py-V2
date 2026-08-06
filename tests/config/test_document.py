"""Test suite for reading, writing & error-reporting of the configuration file."""

import os
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from pydantic import ValidationError

from config import (
    InvalidSettingsFileError,
    SettingsDocument,
    SettingsFileNotFoundError,
    get_settings_file_path,
)
from config._document import (
    PROJECT_ROOT,
    SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME,
)
from config._schema import SettingsSchema

from .conftest import MINIMAL_CONFIG, VALID_BOT_TOKEN

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path
    from typing import Final

    type ConfigWriter = "Callable[[str], Path]"

__all__: "Sequence[str]" = ()


COMMENTED_CONFIG: "Final[str]" = f"""\
# A leading comment about the whole file.

discord:
  # A comment about the bot token.
  bot-token: {VALID_BOT_TOKEN}
  main-guild-id: 1234567890123456789   # A trailing comment.

community-group:
  full-name: Computer Science Society  # Another trailing comment.
  links: {{}}
  msl: {{}}
"""


class TestLoading:
    """Test case for parsing the configuration file."""

    @staticmethod
    def test_valid_file_is_loaded(config_file: "Path") -> None:
        """Test that a valid configuration file is parsed."""
        document: SettingsDocument = SettingsDocument.load(config_file)

        assert document.file_path == config_file
        assert document.raw["discord"]["main-guild-id"] == 1234567890123456789

    @staticmethod
    def test_missing_file_is_reported(tmp_path: "Path") -> None:
        """Test that a configuration file that does not exist is reported clearly."""
        with pytest.raises(SettingsFileNotFoundError):
            SettingsDocument.load(tmp_path / "does-not-exist.yaml")

    @staticmethod
    def test_malformed_yaml_is_reported(write_config: "ConfigWriter") -> None:
        """Test that a file that is not valid YAML is reported clearly."""
        with pytest.raises(InvalidSettingsFileError, match="not a valid YAML file"):
            SettingsDocument.load(write_config("discord:\n  bot-token: [unclosed\n"))

    @staticmethod
    def test_empty_file_is_reported(write_config: "ConfigWriter") -> None:
        """Test that an empty configuration file is reported clearly."""
        with pytest.raises(InvalidSettingsFileError, match="is empty"):
            SettingsDocument.load(write_config(""))

    @staticmethod
    @pytest.mark.parametrize("raw_yaml", ("just-a-string\n", "- one\n- two\n", "42\n"))
    def test_file_without_a_top_level_mapping_is_reported(
        write_config: "ConfigWriter", raw_yaml: str
    ) -> None:
        """Test that a file not holding a mapping of settings is reported clearly."""
        with pytest.raises(InvalidSettingsFileError, match="must contain a mapping"):
            SettingsDocument.load(write_config(raw_yaml))


class TestRoundTripping:
    """Test case for preserving the contents of a hand-written configuration file."""

    @staticmethod
    def test_unmodified_file_is_written_back_unchanged(
        write_config: "ConfigWriter",
    ) -> None:
        """Test that loading & writing a file back leaves it byte-for-byte identical."""
        document: SettingsDocument = SettingsDocument.load(write_config(COMMENTED_CONFIG))

        assert document.dump() == COMMENTED_CONFIG

    @staticmethod
    def test_comments_survive_a_changed_value(write_config: "ConfigWriter") -> None:
        """
        Test that changing a setting preserves every comment around it.

        This is what allows the `/config` command to edit a file that a human wrote &
        annotated, without discarding their annotations.
        """
        config_file_path: Path = write_config(COMMENTED_CONFIG)
        document: SettingsDocument = SettingsDocument.load(config_file_path)

        document.raw["community-group"]["full-name"] = "CompSoc"
        document.write()

        NEW_FILE_CONTENTS: Final[str] = config_file_path.read_text(encoding="utf-8")

        assert "CompSoc" in NEW_FILE_CONTENTS
        assert "# A leading comment about the whole file." in NEW_FILE_CONTENTS
        assert "# A comment about the bot token." in NEW_FILE_CONTENTS
        assert "# A trailing comment." in NEW_FILE_CONTENTS
        assert "# Another trailing comment." in NEW_FILE_CONTENTS

    @staticmethod
    def test_a_long_value_is_not_re_wrapped(write_config: "ConfigWriter") -> None:
        """
        Test that writing a file back does not fold its long values onto extra lines.

        A YAML writer wraps at its configured line width by default, which would rewrite
        untouched sections of the file & bury the one setting that actually changed
        within a diff full of spurious changes.
        """
        LONG_VALUE: Final[str] = " ".join(["a very long channel name"] * 12)

        config_file_path: Path = write_config(
            f"{MINIMAL_CONFIG}commands:\n"
            f"  strike:\n"
            f"    reported-message-destination-channel: {LONG_VALUE}\n"
        )
        document: SettingsDocument = SettingsDocument.load(config_file_path)

        document.raw["community-group"]["full-name"] = "CompSoc"
        document.write()

        assert (
            f"reported-message-destination-channel: {LONG_VALUE}"
            in config_file_path.read_text(encoding="utf-8")
        )

    @staticmethod
    def test_written_file_can_be_loaded_again(write_config: "ConfigWriter") -> None:
        """Test that a rewritten configuration file is still valid."""
        config_file_path: Path = write_config(COMMENTED_CONFIG)
        document: SettingsDocument = SettingsDocument.load(config_file_path)

        document.raw["community-group"]["full-name"] = "CompSoc"
        document.write()

        assert (
            SettingsSchema.model_validate(
                SettingsDocument.load(config_file_path).raw
            ).community_group.full_name
            == "CompSoc"
        )


class TestWriting:
    """Test case for persisting the configuration file to disk."""

    @staticmethod
    def _rejecting_replace(*_args: object, **_kwargs: object) -> None:
        """Stand in for a rename that the filesystem refuses."""
        raise OSError(16, "Device or resource busy")

    @staticmethod
    def test_no_temporary_file_is_left_behind(
        write_config: "ConfigWriter", tmp_path: "Path"
    ) -> None:
        """Test that writing does not leave its temporary file behind."""
        document: SettingsDocument = SettingsDocument.load(write_config(MINIMAL_CONFIG))

        document.write()

        assert not [path for path in tmp_path.iterdir() if path.suffix == ".tmp"]

    @staticmethod
    def test_write_falls_back_when_the_file_cannot_be_replaced(
        write_config: "ConfigWriter", tmp_path: "Path"
    ) -> None:
        """
        Test that a rejected rename falls back to writing the file directly.

        Replacing an individually mounted file within a container is rejected, so the
        fallback is what allows a setting to be saved in that deployment.
        """
        config_file_path: Path = write_config(COMMENTED_CONFIG)
        document: SettingsDocument = SettingsDocument.load(config_file_path)
        document.raw["community-group"]["full-name"] = "FallbackSoc"

        with mock.patch("config._document.os.replace", TestWriting._rejecting_replace):
            document.write()

        NEW_FILE_CONTENTS: Final[str] = config_file_path.read_text(encoding="utf-8")

        assert "FallbackSoc" in NEW_FILE_CONTENTS
        assert "# A leading comment about the whole file." in NEW_FILE_CONTENTS
        assert not [path for path in tmp_path.iterdir() if path.suffix == ".tmp"]

    @staticmethod
    def test_both_write_paths_produce_identical_output(
        write_config: "ConfigWriter", tmp_path: "Path"
    ) -> None:
        """Test that falling back to writing directly produces the same file."""
        atomically_written_path: Path = write_config(COMMENTED_CONFIG)
        atomically_written_document: SettingsDocument = SettingsDocument.load(
            atomically_written_path
        )
        atomically_written_document.raw["community-group"]["full-name"] = "Same"
        atomically_written_document.write()

        directly_written_path: Path = tmp_path / "directly-written.yaml"
        directly_written_path.write_text(COMMENTED_CONFIG, encoding="utf-8")
        directly_written_document: SettingsDocument = SettingsDocument.load(
            directly_written_path
        )
        directly_written_document.raw["community-group"]["full-name"] = "Same"
        with mock.patch("config._document.os.replace", TestWriting._rejecting_replace):
            directly_written_document.write()

        assert atomically_written_path.read_text(
            encoding="utf-8"
        ) == directly_written_path.read_text(encoding="utf-8")

    @staticmethod
    def test_failing_to_write_leaves_the_original_file_intact(
        write_config: "ConfigWriter", tmp_path: "Path"
    ) -> None:
        """Test that a write that fails partway does not damage the existing file."""
        config_file_path: Path = write_config(COMMENTED_CONFIG)
        document: SettingsDocument = SettingsDocument.load(config_file_path)
        document.raw["community-group"]["full-name"] = "ShouldNotAppear"

        with (
            mock.patch(
                "pathlib.Path.write_text", side_effect=OSError(28, "No space left on device")
            ),
            pytest.raises(OSError, match="No space left on device"),
        ):
            document.write()

        assert config_file_path.read_text(encoding="utf-8") == COMMENTED_CONFIG
        assert not [path for path in tmp_path.iterdir() if path.suffix == ".tmp"]


class TestChangingValues:
    """Test case for changing the settings held within a document."""

    @staticmethod
    def test_a_setting_is_written_into_an_absent_section(config_file: "Path") -> None:
        """Test that setting a value creates whichever sections are needed to hold it."""
        document: SettingsDocument = SettingsDocument.load(config_file)

        document.set_value(["reminders", "send-get-roles-reminders", "interval"], "30m")

        assert document.raw["reminders"]["send-get-roles-reminders"]["interval"] == "30m"

    @staticmethod
    def test_a_change_does_not_reach_the_file_until_it_is_written(
        config_file: "Path",
    ) -> None:
        """Test that changing a value alone leaves the file upon disk untouched."""
        document: SettingsDocument = SettingsDocument.load(config_file)

        document.set_value(["community-group", "full-name"], "CompSoc")

        assert config_file.read_text(encoding="utf-8") == MINIMAL_CONFIG

    @staticmethod
    def test_a_setting_cannot_be_written_beneath_a_value(
        write_config: "ConfigWriter",
    ) -> None:
        """Test that a section which holds a plain value is not overwritten silently."""
        document: SettingsDocument = SettingsDocument.load(
            write_config(f"{MINIMAL_CONFIG}commands: not-a-section\n")
        )

        with pytest.raises(InvalidSettingsFileError, match="not a section"):
            document.set_value(["commands", "ping", "easter-egg-probability"], 0.5)

    @staticmethod
    def test_a_setting_must_be_named(config_file: "Path") -> None:
        """Test that changing a value requires a setting to change."""
        document: SettingsDocument = SettingsDocument.load(config_file)

        with pytest.raises(ValueError, match="must be named"):
            document.set_value([], 0.5)

    @staticmethod
    def test_an_absent_setting_is_reported_as_not_removed(config_file: "Path") -> None:
        """Test that removing a setting the file does not hold reports that it did not."""
        document: SettingsDocument = SettingsDocument.load(config_file)

        assert not document.unset_value(["community-group", "full-name"])

    @staticmethod
    def test_a_document_read_again_is_independent_of_the_one_already_held(
        config_file: "Path",
    ) -> None:
        """
        Test that changing a freshly read document leaves an existing one alone.

        A change is applied to the file read afresh & validated before anything is
        written, so a change that turns out to be invalid must not be able to reach the
        configuration that is currently loaded.
        """
        loaded_document: SettingsDocument = SettingsDocument.load(config_file)

        document_being_changed: SettingsDocument = SettingsDocument.load(config_file)
        document_being_changed.set_value(["community-group", "full-name"], "CompSoc")

        assert not loaded_document.contains(["community-group", "full-name"])
        assert document_being_changed.contains(["community-group", "full-name"])


class TestErrorReporting:
    """Test case for pointing a human at the cause of an invalid configuration."""

    @staticmethod
    def test_errors_name_the_line_that_caused_them(write_config: "ConfigWriter") -> None:
        """Test that each validation failure is reported against its source line."""
        document: SettingsDocument = SettingsDocument.load(
            write_config(
                "discord:\n"
                "  bot-token: not-a-real-token\n"
                "  main-guild-id: 12\n"
                "community-group:\n"
                "  links: {}\n"
                "  msl: {}\n"
            )
        )

        with pytest.raises(ValidationError) as validation_error:
            SettingsSchema.model_validate(document.raw)

        FORMATTED_ERROR: Final[str] = document.format_validation_error(validation_error.value)

        assert "tex-bot-deployment.yaml:2" in FORMATTED_ERROR
        assert "tex-bot-deployment.yaml:3" in FORMATTED_ERROR
        assert "discord:bot-token" in FORMATTED_ERROR

    @staticmethod
    def test_errors_never_reveal_the_offending_value(
        write_config: "ConfigWriter",
    ) -> None:
        """Test that a rejected value is not quoted back, in case it is a secret."""
        SECRET_LOOKING_TOKEN: Final[str] = "SUPER-SECRET-BUT-INVALID"  # noqa: S105

        document: SettingsDocument = SettingsDocument.load(
            write_config(
                f"discord:\n"
                f"  bot-token: {SECRET_LOOKING_TOKEN}\n"
                f"  main-guild-id: 1234567890123456789\n"
                f"community-group:\n"
                f"  links: {{}}\n"
                f"  msl: {{}}\n"
            )
        )

        with pytest.raises(ValidationError) as validation_error:
            SettingsSchema.model_validate(document.raw)

        assert SECRET_LOOKING_TOKEN not in document.format_validation_error(
            validation_error.value
        )

    @staticmethod
    def test_a_missing_setting_is_reported_against_its_nearest_section(
        write_config: "ConfigWriter",
    ) -> None:
        """
        Test that an absent setting is still reported against a useful location.

        A setting that is missing entirely has no line of its own, so the closest
        section that does exist is reported instead.
        """
        document: SettingsDocument = SettingsDocument.load(
            write_config(
                "discord:\n"
                "  main-guild-id: 1234567890123456789\n"
                "community-group:\n"
                "  links: {}\n"
                "  msl: {}\n"
            )
        )

        with pytest.raises(ValidationError) as validation_error:
            SettingsSchema.model_validate(document.raw)

        FORMATTED_ERROR: Final[str] = document.format_validation_error(validation_error.value)

        assert "discord:bot-token" in FORMATTED_ERROR
        assert "tex-bot-deployment.yaml:1" in FORMATTED_ERROR

    @staticmethod
    def test_line_numbers_of_absent_settings_are_not_invented(
        config_file: "Path",
    ) -> None:
        """Test that no line is reported for a key path that cannot be resolved at all."""
        document: SettingsDocument = SettingsDocument.load(config_file)

        assert document.line_number_of(["not-a-section", "not-a-setting"]) is None

    @staticmethod
    def test_an_error_within_a_list_is_reported_against_the_list(
        write_config: "ConfigWriter",
    ) -> None:
        """
        Test that a rejected entry of a list is reported against the list holding it.

        Pydantic identifies such an entry by its position, so the reported key path ends
        with a number rather than a name. Individual entries are not resolved to their
        own lines, so the line of the list they belong to is reported instead.
        """
        document: SettingsDocument = SettingsDocument.load(
            write_config(
                f"{MINIMAL_CONFIG}"
                f"commands:\n"
                f"  stats:\n"
                f"    displayed-roles:\n"
                f"      - Committee\n"
                f"      - [a nested list]\n"
            )
        )

        with pytest.raises(ValidationError) as validation_error:
            SettingsSchema.model_validate(document.raw)

        FORMATTED_ERROR: Final[str] = document.format_validation_error(validation_error.value)

        assert "commands:stats:displayed-roles:1" in FORMATTED_ERROR
        assert "tex-bot-deployment.yaml:10" in FORMATTED_ERROR

    @staticmethod
    def test_an_error_with_no_location_is_reported_against_the_whole_file(
        config_file: "Path",
    ) -> None:
        """Test that a failure belonging to no particular setting still names the file."""
        document: SettingsDocument = SettingsDocument.load(config_file)

        with pytest.raises(ValidationError) as validation_error:
            SettingsSchema.model_validate("not a mapping of settings at all")

        FORMATTED_ERROR: Final[str] = document.format_validation_error(validation_error.value)

        assert "(whole file)" in FORMATTED_ERROR
        assert "tex-bot-deployment.yaml" in FORMATTED_ERROR


class TestFileDiscovery:
    """Test case for locating the configuration file."""

    @staticmethod
    def test_environment_variable_is_used_when_set(
        config_file: "Path", monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that the configured environment variable names the file to load."""
        monkeypatch.setenv(SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME, str(config_file))

        assert get_settings_file_path() == config_file.resolve()

    @staticmethod
    def test_missing_file_named_by_the_environment_variable_is_reported(
        tmp_path: "Path", monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that naming a file that does not exist is reported clearly."""
        monkeypatch.setenv(
            SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME, str(tmp_path / "absent.yaml")
        )

        with pytest.raises(SettingsFileNotFoundError, match="environment variable"):
            get_settings_file_path()

    @staticmethod
    def test_absent_configuration_is_reported_with_guidance(
        tmp_path: "Path", monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that finding no configuration at all explains how to provide one."""
        monkeypatch.delenv(SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME, raising=False)
        monkeypatch.setattr("config._document.PROJECT_ROOT", tmp_path)

        with pytest.raises(SettingsFileNotFoundError, match=r"tex-bot-deployment\.yaml"):
            get_settings_file_path()

    @staticmethod
    def test_default_location_is_used_when_no_environment_variable_is_set(
        tmp_path: "Path", monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that the project root is searched when no location is configured."""
        monkeypatch.delenv(SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME, raising=False)
        monkeypatch.setattr("config._document.PROJECT_ROOT", tmp_path)

        DEFAULT_CONFIG_FILE_PATH: Final[Path] = tmp_path / "tex-bot-deployment.yaml"
        DEFAULT_CONFIG_FILE_PATH.write_text(MINIMAL_CONFIG, encoding="utf-8")

        assert get_settings_file_path() == DEFAULT_CONFIG_FILE_PATH.resolve()


class TestExampleConfiguration:
    """Test case for the example configuration file shipped alongside TeX-Bot."""

    @staticmethod
    def _example_config_with_required_settings_filled_in() -> str:
        """Return the example configuration, with its two required values supplied."""
        RAW_EXAMPLE_CONFIG: Final[str] = (
            PROJECT_ROOT / "tex-bot-deployment.example.yaml"
        ).read_text(encoding="utf-8")

        return RAW_EXAMPLE_CONFIG.replace(
            'bot-token: ""', f"bot-token: {VALID_BOT_TOKEN}"
        ).replace("main-guild-id: 0", "main-guild-id: 1234567890123456789")

    @staticmethod
    def test_the_example_configuration_is_valid(write_config: "ConfigWriter") -> None:
        """
        Test that the shipped example validates once its required values are filled in.

        Somebody setting TeX-Bot up copies this file, supplies their token & guild ID,
        and starts it. Every other setting within it must therefore already be valid as
        written, including each one that is only there to show what it would look like.
        """
        document: SettingsDocument = SettingsDocument.load(
            write_config(
                TestExampleConfiguration._example_config_with_required_settings_filled_in()
            )
        )

        SettingsSchema.model_validate(document.raw)

    @staticmethod
    def test_the_example_configuration_leaves_optional_settings_absent(
        write_config: "ConfigWriter",
    ) -> None:
        """
        Test that the example supplies no placeholder in place of an optional setting.

        A setting that is present must hold a valid value, so a placeholder such as `""`
        is rejected rather than treated as the setting having been left unset.
        """
        settings: SettingsSchema = SettingsSchema.model_validate(
            SettingsDocument.load(
                write_config(
                    TestExampleConfiguration._example_config_with_required_settings_filled_in()
                )
            ).raw
        )

        assert settings.community_group.full_name is None
        assert settings.community_group.links.purchase_membership is None
        assert settings.community_group.msl.organisation_id is None
        assert settings.community_group.msl.auth_cookie is None


def test_temporary_file_is_written_alongside_its_destination(config_file: "Path") -> None:
    """
    Test that the temporary file used while writing is created beside the destination.

    Renaming is only atomic within a single filesystem, which writing alongside the
    destination guarantees.
    """
    document: SettingsDocument = SettingsDocument.load(config_file)

    observed_temporary_paths: list[str] = []
    real_replace = os.replace

    def _recording_replace(src: object, dst: object) -> None:
        observed_temporary_paths.append(str(src))
        real_replace(src, dst)  # type: ignore[arg-type]

    with mock.patch("config._document.os.replace", _recording_replace):
        document.write()

    assert len(observed_temporary_paths) == 1
    assert (
        os.path.dirname(observed_temporary_paths[0])  # noqa: PTH120
        == str(config_file.parent)
    )
