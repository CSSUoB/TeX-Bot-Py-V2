"""Test suite for the settings schema."""

import datetime
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from config import get_settings_metadata
from config._schema import LogLevel, SettingsSchema

from .conftest import (
    DEFAULT_EASTER_EGG_PROBABILITY,
    MINIMAL_CONFIG,
    VALID_BOT_TOKEN,
    VALID_MAIN_GUILD_ID,
    VALID_WEBHOOK_URL,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Final

    from config import ConfigSettingMetadata

__all__: "Sequence[str]" = ()


REQUIRED_SETTINGS: "Final[Mapping[str, object]]" = {
    "discord": {"bot-token": VALID_BOT_TOKEN, "main-guild-id": VALID_MAIN_GUILD_ID},
    "community-group": {"links": {}, "msl": {}},
}


def _config(**overrides: object) -> "Mapping[str, object]":
    """Build a valid raw configuration, with the given top-level sections replaced."""
    return {**REQUIRED_SETTINGS, **overrides}


class TestRequiredSettings:
    """Test case for which settings a configuration must provide."""

    @staticmethod
    def test_minimal_configuration_is_valid() -> None:
        """Test that a configuration holding only the required settings validates."""
        settings: SettingsSchema = SettingsSchema.model_validate(_config())

        assert settings.discord.main_guild_id == VALID_MAIN_GUILD_ID

    @staticmethod
    @pytest.mark.parametrize("missing_section", ("discord", "community-group"))
    def test_missing_required_section_is_rejected(missing_section: str) -> None:
        """Test that omitting a required section is rejected."""
        raw_settings: dict[str, object] = dict(REQUIRED_SETTINGS)
        del raw_settings[missing_section]

        with pytest.raises(ValidationError, match="Field required"):
            SettingsSchema.model_validate(raw_settings)

    @staticmethod
    def test_unknown_setting_is_rejected() -> None:
        """Test that a setting the schema does not declare is rejected."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            SettingsSchema.model_validate(_config(**{"not-a-real-setting": True}))

    @staticmethod
    def test_every_optional_section_may_be_omitted() -> None:
        """Test that omitting every optional section still produces usable defaults."""
        settings: SettingsSchema = SettingsSchema.model_validate(_config())

        assert settings.logging.console.log_level == LogLevel.INFO
        assert settings.commands.ping.easter_egg_probability == DEFAULT_EASTER_EGG_PROBABILITY
        assert settings.reminders.send_get_roles_reminders.enabled is True
        assert settings.auto_add_committee_to_threads is True

    @staticmethod
    def test_discord_log_channel_section_is_optional() -> None:
        """
        Test that the Discord log-channel section may be omitted from within `logging`.

        This section holds a required webhook URL, so it must be possible to configure
        other logging destinations without providing one.
        """
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(logging={"console": {"log-level": "DEBUG"}})
        )

        assert settings.logging.discord_channel is None
        assert settings.logging.console.log_level == LogLevel.DEBUG

    @staticmethod
    def test_discord_log_channel_requires_a_webhook_url() -> None:
        """Test that providing the Discord log-channel section requires a webhook URL."""
        with pytest.raises(ValidationError, match="Field required"):
            SettingsSchema.model_validate(
                _config(logging={"discord-channel": {"log-level": "ERROR"}})
            )


class TestDurationParsing:
    """Test case for parsing the delay/interval strings used by time-based settings."""

    @staticmethod
    @pytest.mark.parametrize(
        ("raw_duration", "expected_duration"),
        (
            ("30s", datetime.timedelta(seconds=30)),
            ("10m", datetime.timedelta(minutes=10)),
            ("24h", datetime.timedelta(hours=24)),
            ("2d", datetime.timedelta(days=2)),
            ("1h30m", datetime.timedelta(hours=1, minutes=30)),
            ("90m", datetime.timedelta(minutes=90)),
            ("1d12h30m15s", datetime.timedelta(days=1, hours=12, minutes=30, seconds=15)),
            ("0.5h", datetime.timedelta(minutes=30)),
        ),
    )
    def test_valid_durations_are_parsed(
        raw_duration: str, expected_duration: datetime.timedelta
    ) -> None:
        """Test that a duration written largest-unit-first is parsed."""
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(commands={"strike": {"timeout-duration": raw_duration}})
        )

        assert settings.commands.strike.timeout_duration == expected_duration

    @staticmethod
    @pytest.mark.parametrize(
        "raw_duration",
        (
            "30m1h",  # NOTE: Units given smallest-first
            "1h 30m",  # NOTE: Whitespace between units
            "",  # NOTE: An empty string is not a duration
            "PT1H30M",  # NOTE: An ISO-8601 duration
            "01:30:00",
            "5",  # NOTE: No unit given
            "5x",  # NOTE: An unknown unit
            "-1h",
        ),
    )
    def test_invalid_durations_are_rejected(raw_duration: str) -> None:
        """Test that anything outside the documented duration format is rejected."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(commands={"strike": {"timeout-duration": raw_duration}})
            )

    @staticmethod
    def test_an_already_parsed_duration_is_kept() -> None:
        """
        Test that a value that is already a length of time is accepted unchanged.

        Each default value is re-validated whenever the model holding it is rebuilt, so
        rejecting anything that is not a string would reject the schema's own defaults.
        """
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(commands={"strike": {"timeout-duration": datetime.timedelta(hours=3)}})
        )

        assert settings.commands.strike.timeout_duration == datetime.timedelta(hours=3)


class TestZeroLengthDurations:
    """Test case for durations of no length at all."""

    @staticmethod
    @pytest.mark.parametrize("raw_duration", ("0s", "0m", "0d0h0m0s", "0.0s"))
    def test_a_zero_length_interval_is_rejected(raw_duration: str) -> None:
        """
        Test that an interval of no length at all is rejected.

        Each interval becomes the loop period of a recurring task, so a zero-length one
        would cause that task to run continuously without ever pausing. Rejecting only
        the empty string is not enough, because `0s` is written deliberately.
        """
        with pytest.raises(ValidationError, match="longer than zero"):
            SettingsSchema.model_validate(
                _config(reminders={"send-get-roles-reminders": {"interval": raw_duration}})
            )

    @staticmethod
    @pytest.mark.parametrize(
        "raw_settings",
        (
            {
                "community-group": {
                    "links": {},
                    "msl": {"auto-cookie-checking": {"interval": "0s"}},
                }
            },
            {"reminders": {"send-introduction-reminders": {"interval": "0s"}}},
            {"reminders": {"send-get-roles-reminders": {"interval": "0s"}}},
        ),
    )
    def test_every_task_interval_rejects_a_zero_length_duration(
        raw_settings: "Mapping[str, object]",
    ) -> None:
        """Test that no recurring task can be configured to loop without pausing."""
        with pytest.raises(ValidationError, match="longer than zero"):
            SettingsSchema.model_validate({**REQUIRED_SETTINGS, **raw_settings})

    @staticmethod
    def test_a_zero_length_delay_is_accepted() -> None:
        """
        Test that waiting no time at all before sending a reminder is allowed.

        Unlike an interval, a delay of zero is a meaningful instruction: send the
        reminder as soon as the member becomes eligible for it.
        """
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(reminders={"send-get-roles-reminders": {"delay": "0s"}})
        )

        assert settings.reminders.send_get_roles_reminders.delay == datetime.timedelta(0)


class TestValueConstraints:
    """Test case for the constraints applied to individual settings values."""

    @staticmethod
    @pytest.mark.parametrize("probability", (0, 0.5, 1))
    def test_easter_egg_probability_accepts_its_range(probability: float) -> None:
        """Test that a probability within zero to one inclusive is accepted."""
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(commands={"ping": {"easter-egg-probability": probability}})
        )

        assert settings.commands.ping.easter_egg_probability == probability

    @staticmethod
    @pytest.mark.parametrize("probability", (-0.1, 1.1, 100))
    def test_easter_egg_probability_rejects_values_outside_its_range(
        probability: float,
    ) -> None:
        """Test that a probability outside zero to one inclusive is rejected."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(commands={"ping": {"easter-egg-probability": probability}})
            )

    @staticmethod
    @pytest.mark.parametrize("guild_id", (10**16 - 1, 10**20, 0, -1))
    def test_invalid_discord_snowflake_is_rejected(guild_id: int) -> None:
        """Test that an ID outside the range of a Discord snowflake is rejected."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                {
                    **REQUIRED_SETTINGS,
                    "discord": {"bot-token": VALID_BOT_TOKEN, "main-guild-id": guild_id},
                }
            )

    @staticmethod
    @pytest.mark.parametrize(
        "bot_token",
        ("", "not-a-token", "short.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs", VALID_BOT_TOKEN[:-1]),
    )
    def test_invalid_bot_token_is_rejected(bot_token: str) -> None:
        """Test that a value not matching the Discord bot-token format is rejected."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                {
                    **REQUIRED_SETTINGS,
                    "discord": {"bot-token": bot_token, "main-guild-id": VALID_MAIN_GUILD_ID},
                }
            )

    @staticmethod
    @pytest.mark.parametrize("separator", ("--", "__"))
    def test_bot_token_containing_repeated_punctuation_is_rejected(separator: str) -> None:
        """
        Test that a token holding two consecutive hyphens or underscores is rejected.

        Discord never issues such a token, so one appearing here almost always means a
        placeholder has been left in place of a real token.
        """
        REPEATED_PUNCTUATION_TOKEN: Final[str] = (
            f"{VALID_BOT_TOKEN[:-4]}{separator}{VALID_BOT_TOKEN[-2:]}"
        )

        with pytest.raises(ValidationError, match="Discord bot token"):
            SettingsSchema.model_validate(
                {
                    **REQUIRED_SETTINGS,
                    "discord": {
                        "bot-token": REPEATED_PUNCTUATION_TOKEN,
                        "main-guild-id": VALID_MAIN_GUILD_ID,
                    },
                }
            )

    @staticmethod
    def test_bot_token_containing_differing_punctuation_is_accepted() -> None:
        """Test that a hyphen adjacent to an underscore is not treated as a repetition."""
        MIXED_PUNCTUATION_TOKEN: Final[str] = f"{VALID_BOT_TOKEN[:-4]}-_{VALID_BOT_TOKEN[-2:]}"

        settings: SettingsSchema = SettingsSchema.model_validate(
            {
                **REQUIRED_SETTINGS,
                "discord": {
                    "bot-token": MIXED_PUNCTUATION_TOKEN,
                    "main-guild-id": VALID_MAIN_GUILD_ID,
                },
            }
        )

        assert settings.discord.bot_token.get_secret_value() == MIXED_PUNCTUATION_TOKEN

    @staticmethod
    @pytest.mark.parametrize("lookback_days", (5, 1826))
    def test_statistics_lookback_accepts_its_range(lookback_days: int) -> None:
        """Test that a lookback within five days to five years inclusive is accepted."""
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(commands={"stats": {"lookback-days": lookback_days}})
        )

        assert settings.commands.stats.lookback_days == lookback_days

    @staticmethod
    @pytest.mark.parametrize("lookback_days", (4, 1827, 0, -1))
    def test_statistics_lookback_rejects_values_outside_its_range(lookback_days: int) -> None:
        """Test that a lookback outside five days to five years inclusive is rejected."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(commands={"stats": {"lookback-days": lookback_days}})
            )

    @staticmethod
    @pytest.mark.parametrize("organisation_id", ("123", "123456", "12a4", "", "1234 "))
    def test_invalid_msl_organisation_id_is_rejected(organisation_id: str) -> None:
        """Test that an organisation ID that is not four or five digits is rejected."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(
                    **{
                        "community-group": {
                            "links": {},
                            "msl": {"organisation-id": organisation_id},
                        }
                    }
                )
            )

    @staticmethod
    @pytest.mark.parametrize(
        ("setting_name", "value_with_trailing_newline"),
        (("organisation-id", "1234\n"), ("auth-cookie", f"{'a' * 512}\n")),
    )
    def test_a_trailing_newline_does_not_satisfy_a_pattern(
        setting_name: str, value_with_trailing_newline: str
    ) -> None:
        r"""
        Test that a value is not accepted merely because its first line would be.

        Every pattern is anchored with `\Z` rather than `$`, so that a trailing newline
        cannot smuggle an otherwise-rejected value through. This is why the schema uses
        Python's regular-expression engine, rather than the Rust engine Pydantic
        defaults to, which does not support that anchor.
        """
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(
                    **{
                        "community-group": {
                            "links": {},
                            "msl": {setting_name: value_with_trailing_newline},
                        }
                    }
                )
            )

    @staticmethod
    def test_non_discord_webhook_url_is_rejected() -> None:
        """Test that a URL that is not a Discord webhook is rejected."""
        with pytest.raises(ValidationError, match="Discord webhook URL"):
            SettingsSchema.model_validate(
                _config(logging={"discord-channel": {"webhook-url": "https://example.com"}})
            )

    @staticmethod
    def test_discord_webhook_url_is_accepted() -> None:
        """Test that a Discord webhook URL is accepted."""
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(logging={"discord-channel": {"webhook-url": VALID_WEBHOOK_URL}})
        )

        assert settings.logging.discord_channel is not None
        assert str(settings.logging.discord_channel.webhook_url).startswith(
            "https://discord.com/api/webhooks/"
        )

    @staticmethod
    def test_a_sequence_of_distinct_values_is_accepted() -> None:
        """Test that a list of role names holding no repetitions is kept as written."""
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(
                **{
                    "community-group": {
                        "links": {},
                        "msl": {},
                        "membership-dependent-roles": ["Member", "Committee"],
                    }
                }
            )
        )

        assert settings.community_group.membership_dependent_roles == ("Member", "Committee")

    @staticmethod
    def test_duplicate_values_within_a_unique_sequence_are_rejected() -> None:
        """Test that repeating a value within a set of role names is rejected."""
        with pytest.raises(ValidationError, match="unique"):
            SettingsSchema.model_validate(
                _config(commands={"stats": {"displayed-roles": ["Member", "Member"]}})
            )


class TestValueNormalisation:
    """Test case for values that are accepted in more than one form."""

    @staticmethod
    @pytest.mark.parametrize(
        "raw_log_level", ("DEBUG", "debug", " Debug ", "-debug-", "debug.")
    )
    def test_log_level_is_matched_case_and_punctuation_agnostically(
        raw_log_level: str,
    ) -> None:
        """Test that a log level is recognised regardless of case or stray punctuation."""
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(logging={"console": {"log-level": raw_log_level}})
        )

        assert settings.logging.console.log_level == LogLevel.DEBUG

    @staticmethod
    def test_unknown_log_level_is_rejected() -> None:
        """Test that a value that is not a log level is rejected."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(logging={"console": {"log-level": "NONSENSE"}})
            )

    @staticmethod
    @pytest.mark.parametrize(
        ("raw_flag", "expected_flag"),
        (
            ("once", "once"),
            ("interval", "interval"),
            (True, "once"),
            ("true", "once"),
            ("yes", "once"),
            ("on", "once"),
            ("1", "once"),
            (" Once ", "once"),
            (False, False),
            ("false", False),
            ("no", False),
            ("off", False),
            ("0", False),
        ),
    )
    def test_send_introduction_reminders_flag_is_normalised(
        raw_flag: object, expected_flag: object
    ) -> None:
        """Test that boolean-like values are treated as their canonical equivalent."""
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(reminders={"send-introduction-reminders": {"enabled": raw_flag}})
        )

        assert settings.reminders.send_introduction_reminders.enabled == expected_flag

    @staticmethod
    @pytest.mark.parametrize("raw_flag", ("maybe", "sometimes", "ONCE-ish"))
    def test_an_unrecognised_reminders_flag_string_is_rejected(raw_flag: str) -> None:
        """Test that a string outside the recognised options is not quietly accepted."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(reminders={"send-introduction-reminders": {"enabled": raw_flag}})
            )

    @staticmethod
    def test_lookback_days_is_exposed_as_a_period() -> None:
        """Test that the statistics lookback is usable as a length of time."""
        settings: SettingsSchema = SettingsSchema.model_validate(
            _config(commands={"stats": {"lookback-days": 14}})
        )

        assert settings.commands.stats.lookback_period == datetime.timedelta(days=14)


class TestSecrecy:
    """Test case for keeping secret settings out of logs & error messages."""

    @staticmethod
    def test_secret_values_are_masked_when_displayed() -> None:
        """Test that a secret value is not revealed by displaying the settings."""
        settings: SettingsSchema = SettingsSchema.model_validate(_config())

        assert VALID_BOT_TOKEN not in repr(settings)
        assert VALID_BOT_TOKEN not in str(settings.discord.bot_token)

    @staticmethod
    def test_secret_values_remain_readable_when_explicitly_requested() -> None:
        """Test that a secret value can still be read where it is genuinely needed."""
        settings: SettingsSchema = SettingsSchema.model_validate(_config())

        assert settings.discord.bot_token.get_secret_value() == VALID_BOT_TOKEN

    @staticmethod
    def test_rejected_secret_value_is_absent_from_scrubbed_errors() -> None:
        """Test that an invalid secret is not echoed back by a scrubbed error message."""
        invalid_token: Final[str] = "SUPER-SECRET-BUT-INVALID"  # noqa: S105

        with pytest.raises(ValidationError) as validation_error:
            SettingsSchema.model_validate(
                {
                    **REQUIRED_SETTINGS,
                    "discord": {
                        "bot-token": invalid_token,
                        "main-guild-id": VALID_MAIN_GUILD_ID,
                    },
                }
            )

        assert invalid_token not in str(
            validation_error.value.errors(include_input=False, include_url=False)
        )


class TestSettingsMetadata:
    """Test case for the metadata describing each setting to a human."""

    @staticmethod
    def test_every_setting_is_described() -> None:
        """Test that no setting is missing its help text."""
        undescribed_settings: Sequence[str] = [
            settings_name
            for settings_name, metadata in get_settings_metadata().items()
            if not metadata.description
        ]

        assert not undescribed_settings

    @staticmethod
    def test_settings_requiring_a_restart_are_exactly_those_that_cannot_be_applied() -> None:
        """
        Test that only the settings which genuinely cannot be applied need a restart.

        Flagging a setting that could be applied would send committee members away to
        restart TeX-Bot for no reason, and failing to flag one that cannot would leave
        them believing a change had taken effect when it had not.
        """
        EXPECTED_RESTART_REQUIRED_SETTINGS: Final[frozenset[str]] = frozenset(
            {
                # NOTE: Used to connect to Discord & to populate the shortcut accessors.
                "discord:bot-token",
                "discord:main-guild-id",
                # NOTE: Fixed when each recurring task is created during start-up.
                "community-group:msl:auto-cookie-checking:enabled",
                "community-group:msl:auto-cookie-checking:interval",
                "reminders:send-introduction-reminders:enabled",
                "reminders:send-introduction-reminders:interval",
                "reminders:send-get-roles-reminders:enabled",
                "reminders:send-get-roles-reminders:interval",
            }
        )

        assert (
            frozenset(
                settings_name
                for settings_name, metadata in get_settings_metadata().items()
                if metadata.requires_restart
            )
            == EXPECTED_RESTART_REQUIRED_SETTINGS
        )

    @staticmethod
    def test_delays_do_not_require_a_restart() -> None:
        """
        Test that the delay before a reminder is sent takes effect without a restart.

        Unlike the interval of the task that sends them, a delay is read from the
        settings accessor at the moment it is used.
        """
        SETTINGS_METADATA: Final[Mapping[str, ConfigSettingMetadata]] = get_settings_metadata()

        assert not SETTINGS_METADATA[
            "reminders:send-introduction-reminders:delay"
        ].requires_restart
        assert not SETTINGS_METADATA[
            "reminders:send-get-roles-reminders:delay"
        ].requires_restart

    @staticmethod
    def test_every_secret_setting_is_flagged() -> None:
        """Test that each setting holding a credential is marked as secret."""
        EXPECTED_SECRET_SETTINGS: Final[frozenset[str]] = frozenset(
            {
                "discord:bot-token",
                "community-group:msl:auth-cookie",
                "logging:discord-channel:webhook-url",
            }
        )

        assert (
            frozenset(
                settings_name
                for settings_name, metadata in get_settings_metadata().items()
                if metadata.secret
            )
            == EXPECTED_SECRET_SETTINGS
        )

    @staticmethod
    def test_metadata_covers_every_configurable_setting() -> None:
        """Test that the metadata describes exactly the settings that can be configured."""
        from config._accessor import _flatten_settings  # noqa: PLC0415

        SETTINGS_NAMES: Final[frozenset[str]] = frozenset(
            _flatten_settings(SettingsSchema.model_validate(_config()))
        )

        # NOTE: An omitted optional section collapses to a single key, so the metadata
        # describes the sections within it that the flattened settings cannot show.
        assert SETTINGS_NAMES - frozenset(get_settings_metadata()) == {
            "logging:discord-channel"
        }


def test_minimal_config_fixture_matches_the_required_settings() -> None:
    """Test that the shared minimal configuration holds exactly what the schema requires."""
    assert "bot-token" in MINIMAL_CONFIG
    assert "main-guild-id" in MINIMAL_CONFIG


class TestNonStringValues:
    """Test case for values given as the wrong type entirely."""

    @staticmethod
    @pytest.mark.parametrize("raw_duration", (30, 1.5, True, None, ["1h"]))
    def test_a_duration_that_is_not_a_string_is_rejected(raw_duration: object) -> None:
        """Test that a duration must be written as a string, not a bare number."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(commands={"strike": {"timeout-duration": raw_duration}})
            )

    @staticmethod
    @pytest.mark.parametrize("raw_log_level", (10, None, ["DEBUG"]))
    def test_a_log_level_that_is_not_a_string_is_rejected(raw_log_level: object) -> None:
        """Test that a log level must be written as one of its names."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(logging={"console": {"log-level": raw_log_level}})
            )

    @staticmethod
    @pytest.mark.parametrize("raw_flag", (42, None, ["once"], 0, 1))
    def test_an_unrecognised_reminders_flag_is_rejected(raw_flag: object) -> None:
        """
        Test that a send-introduction-reminders value outside its options is rejected.

        `0` is included because Pydantic would otherwise accept it as `False` while
        rejecting the `1` its author would pair it with, silently disabling introduction
        reminders for anyone who wrote them as numbers.
        """
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(reminders={"send-introduction-reminders": {"enabled": raw_flag}})
            )

    @staticmethod
    def test_a_webhook_url_that_is_not_a_url_is_rejected() -> None:
        """Test that the Discord log-channel webhook must be a URL."""
        with pytest.raises(ValidationError):
            SettingsSchema.model_validate(
                _config(logging={"discord-channel": {"webhook-url": 42}})
            )
