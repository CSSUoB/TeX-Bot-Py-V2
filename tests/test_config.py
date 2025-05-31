"""Automated test suite for the `Settings` class & related functions within `config.py`."""

import functools
import itertools
import json
import logging
import os
import random
import re
import string
from collections.abc import Iterable
from datetime import timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

import pytest

import config
from config import Settings
from exceptions import (
    ImproperlyConfiguredError,
    MessagesJSONFileMissingKeyError,
    MessagesJSONFileValueError,
)
from utils import (
    EnvVariableDeleter,
    FileTemporaryDeleter,
    RandomDiscordBotTokenGenerator,
    RandomDiscordGuildIDGenerator,
    RandomDiscordLogChannelWebhookURLGenerator,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import IO, Final, TextIO

    from _pytest._code import ExceptionInfo
    from _pytest.logging import LogCaptureFixture


class TestSettings:
    """Test case to unit-test the `Settings` class & its instances."""

    @classmethod
    def replace_setup_methods(
        cls,
        ignore_methods: Iterable[str] | None = None,
        replacement_method: "Callable[[str], None] | None" = None,
    ) -> type[Settings]:
        """Return a new runtime version of the `Settings` class, with replaced methods."""
        if ignore_methods is None:
            ignore_methods = set()

        def empty_setup_method() -> None:
            pass

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        SETUP_METHOD_NAMES: Final[Iterable[str]] = {
            setup_method_name
            for setup_method_name in dir(RuntimeSettings)
            if (
                setup_method_name.startswith("_setup_")
                and setup_method_name not in ignore_methods
            )
        }

        if not SETUP_METHOD_NAMES:  # type: ignore[truthy-iterable]
            NO_SETUP_METHOD_NAMES_MESSAGE: Final[str] = "No setup methods"
            raise RuntimeError(NO_SETUP_METHOD_NAMES_MESSAGE)

        setup_method_name: str
        for setup_method_name in SETUP_METHOD_NAMES:
            setattr(
                RuntimeSettings,
                setup_method_name,
                (
                    functools.partial(replacement_method, setup_method_name)
                    if replacement_method is not None
                    else empty_setup_method
                ),
            )

        return RuntimeSettings

    @pytest.mark.parametrize("test_item_name", ("ITEM_1",))
    @pytest.mark.parametrize("test_item_value", ("value_1",))
    def test_getattr_success(self, test_item_name: str, test_item_value: str) -> None:
        """Test that retrieving a settings variable by attr-lookup returns the set value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        RuntimeSettings._settings[test_item_name] = test_item_value
        RuntimeSettings._is_env_variables_setup = True

        assert getattr(RuntimeSettings(), test_item_name) == test_item_value

    @pytest.mark.parametrize("missing_item_name", ("ITEM",))
    def test_getattr_missing_item(self, missing_item_name: str) -> None:
        """
        Test that requesting a missing settings variable by attribute-lookup raises an error.

        A missing settings variable is one that has a valid name,
        but does not exist within the `_settings` dict (i.e. has not been set).
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._is_env_variables_setup = True

        with pytest.raises(
            AttributeError, match=f"'{missing_item_name}' is not a valid settings key."
        ):
            assert getattr(RuntimeSettings(), missing_item_name)

    @pytest.mark.parametrize("invalid_item_name", ("item_1", "ITEM__1", "!ITEM_1"))
    def test_getattr_invalid_name(self, invalid_item_name: str) -> None:
        """Test that requesting an invalid settings variable by attr-lookup raises an error."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        RuntimeSettings._is_env_variables_setup = True

        with pytest.raises(AttributeError, match=f"no attribute {invalid_item_name!r}"):
            assert getattr(RuntimeSettings(), invalid_item_name)

    @pytest.mark.parametrize("test_item_name", ("ITEM_1",))
    @pytest.mark.parametrize("test_item_value", ("value_1",))
    def test_getattr_sets_up_env_variables(
        self, test_item_name: str, test_item_value: str
    ) -> None:
        """
        Test that requesting a settings variable sets them all up if they have not been.

        This test requests the settings variable by attribute-lookup.
        """
        is_env_variables_setup: bool = False

        def set_is_env_variables_setup(_instance: Settings | None = None) -> None:
            nonlocal is_env_variables_setup
            is_env_variables_setup = True

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._settings[test_item_name] = test_item_value
        RuntimeSettings._setup_env_variables = set_is_env_variables_setup  # type: ignore[method-assign]

        getattr(RuntimeSettings(), test_item_name)

        assert is_env_variables_setup is True

    @pytest.mark.parametrize("test_item_name", ("ITEM_1",))
    @pytest.mark.parametrize("test_item_value", ("value_1",))
    def test_getitem_success(self, test_item_name: str, test_item_value: str) -> None:
        """Test that retrieving a settings variable by key-lookup returns the set value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        RuntimeSettings._settings[test_item_name] = test_item_value
        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()[test_item_name] == test_item_value

    @pytest.mark.parametrize("missing_item_name", ("ITEM",))
    def test_getitem_missing_item(self, missing_item_name: str) -> None:
        """
        Test that requesting a missing settings variable by key-lookup raises an error.

        A missing settings variable is one that has a valid name,
        but does not exist within the `_settings` dict (i.e. has not been set).
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._is_env_variables_setup = True

        with pytest.raises(
            KeyError, match=f"'{missing_item_name}' is not a valid settings key."
        ):
            assert RuntimeSettings()[missing_item_name]

    @pytest.mark.parametrize("invalid_item_name", ("item_1", "ITEM__1", "!ITEM_1"))
    def test_getitem_invalid_name(self, invalid_item_name: str) -> None:
        """Test that requesting an invalid settings variable by key-lookup raises an error."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._is_env_variables_setup = True

        with pytest.raises(KeyError, match=str(KeyError(invalid_item_name))):
            assert RuntimeSettings()[invalid_item_name]

    @pytest.mark.parametrize("test_item_name", ("ITEM_1",))
    @pytest.mark.parametrize("test_item_value", ("value_1",))
    def test_getitem_sets_up_env_variables(
        self,
        test_item_name: str,
        test_item_value: str,
    ) -> None:
        """
        Test that requesting a settings variable sets them all up if they have not been.

        This test requests the settings variable by key-lookup.
        """
        is_env_variables_setup: bool = False

        def set_is_env_variables_setup(_instance: Settings | None = None) -> None:
            nonlocal is_env_variables_setup
            is_env_variables_setup = True

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._settings[test_item_name] = test_item_value
        RuntimeSettings._setup_env_variables = set_is_env_variables_setup  # type: ignore[method-assign]

        RuntimeSettings().__getitem__(test_item_name)

        assert is_env_variables_setup is True

    def test_is_env_variables_setup_made_true(self) -> None:
        """Test calling `_setup_env_variables()` sets `_is_env_variables_setup` to True."""
        RuntimeSettings: Final[type[Settings]] = self.replace_setup_methods(
            ignore_methods=("_setup_env_variables",),
        )

        assert RuntimeSettings._is_env_variables_setup is False

        RuntimeSettings._setup_env_variables()

        assert RuntimeSettings._is_env_variables_setup is True

    def test_every_setup_method_called(self) -> None:
        """Test that calling `_setup_env_variables()` sets up all Env Variables."""
        CALLED_SETUP_METHODS: Final[set[str]] = set()

        def add_called_setup_method(setup_method_name: str) -> None:
            nonlocal CALLED_SETUP_METHODS
            CALLED_SETUP_METHODS.add(setup_method_name)

        RuntimeSettings: Final[type[Settings]] = self.replace_setup_methods(
            ignore_methods=("_setup_env_variables",),
            replacement_method=add_called_setup_method,
        )

        RuntimeSettings._setup_env_variables()

        assert (
            CALLED_SETUP_METHODS  # noqa: SIM300
            == {
                setup_method_name
                for setup_method_name in dir(RuntimeSettings)
                if (
                    setup_method_name.startswith("_setup_")
                    and setup_method_name != "_setup_env_variables"
                )
            }
        )

    @pytest.mark.parametrize("test_item_name", ("ITEM_1",))
    @pytest.mark.parametrize("test_item_value", ("value_1",))
    def test_cannot_setup_more_than_once(
        self,
        caplog: "LogCaptureFixture",
        test_item_name: str,
        test_item_value: str,
    ) -> None:
        """Test that the Env Variables cannot be set more than once."""
        RuntimeSettings: Final[type[Settings]] = self.replace_setup_methods(
            ignore_methods=("_setup_env_variables",),
        )

        RuntimeSettings._setup_env_variables()
        RuntimeSettings._settings[test_item_name] = test_item_value

        PREVIOUS_SETTINGS: Final[dict[str, object]] = RuntimeSettings._settings.copy()

        assert not caplog.text

        RuntimeSettings._setup_env_variables()

        assert RuntimeSettings._settings == PREVIOUS_SETTINGS
        assert "already" in caplog.text
        assert "set up" in caplog.text

    def test_module_level_settings_object(self) -> None:
        """Test that the auto-instantiated module-level settings object is correct."""
        assert isinstance(config.settings, Settings)

    def test_settings_class_factory(self) -> None:
        """Test that the settings class factory produces valid & separate settings classes."""
        assert issubclass(config._settings_class_factory(), Settings)

        assert config._settings_class_factory()._is_env_variables_setup is False
        assert not config._settings_class_factory()._settings

        assert config._settings_class_factory() != config._settings_class_factory()


class TestSetupLogging:
    """Test case to unit-test the `_setup_logging()` function."""

    @pytest.mark.parametrize("test_log_level", config.LOG_LEVEL_CHOICES)
    def test_setup_logging_successful(self, test_log_level: str) -> None:
        """Test that the given `CONSOLE_LOG_LEVEL` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = test_log_level

            RuntimeSettings._setup_logging()

        assert "TeX-Bot" in set(logging.root.manager.loggerDict)
        assert logging.getLogger("TeX-Bot").getEffectiveLevel() == getattr(
            logging, test_log_level
        )

    def test_default_console_log_level(self) -> None:
        """Test that a default value is used when no `CONSOLE_LOG_LEVEL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            RuntimeSettings._setup_logging()

        assert "TeX-Bot" in set(logging.root.manager.loggerDict)

    @pytest.mark.parametrize(
        "invalid_log_level",
        (
            "invalid_log_level",
            "",
            "  ",
            "".join(
                random.choices(
                    string.ascii_letters + string.digits + string.punctuation,
                    k=18,
                ),
            ),
        ),
        ids=[f"case_{i}" for i in range(4)],
    )
    def test_invalid_console_log_level(self, invalid_log_level: str) -> None:
        """Test that an error is raised when an invalid `CONSOLE_LOG_LEVEL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = invalid_log_level

            with pytest.raises(ImproperlyConfiguredError, match="LOG_LEVEL must be one of"):
                RuntimeSettings._setup_logging()

    @pytest.mark.parametrize("lower_case_log_level", ("info",))
    def test_valid_lowercase_console_log_level(self, lower_case_log_level: str) -> None:
        """Test that the provided `CONSOLE_LOG_LEVEL` is fixed & used if it is in lowercase."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = lower_case_log_level

            RuntimeSettings._setup_logging()


class TestSetupDiscordBotToken:
    """Test case to unit-test the `_setup_discord_bot_token()` function."""

    @pytest.mark.parametrize(
        "test_discord_bot_token",
        itertools.chain(
            RandomDiscordBotTokenGenerator.multiple_values(),
            (f"    {RandomDiscordBotTokenGenerator.single_value()}   ",),
        ),
        ids=[f"case_{i}" for i in range(6)],
    )
    def test_setup_discord_bot_token_successful(self, test_discord_bot_token: str) -> None:
        """Test that the given `DISCORD_BOT_TOKEN` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("DISCORD_BOT_TOKEN"):
            os.environ["DISCORD_BOT_TOKEN"] = test_discord_bot_token

            RuntimeSettings._setup_discord_bot_token()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["DISCORD_BOT_TOKEN"] == test_discord_bot_token.strip()

    def test_missing_discord_bot_token(self) -> None:
        """Test that an error is raised when no `DISCORD_BOT_TOKEN` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("DISCORD_BOT_TOKEN"):  # noqa: SIM117
            with pytest.raises(
                ImproperlyConfiguredError, match=r"DISCORD_BOT_TOKEN.*valid.*Discord bot token"
            ):
                RuntimeSettings._setup_discord_bot_token()

    @pytest.mark.parametrize(
        "invalid_discord_bot_token",
        (
            "invalid_discord_bot_token",
            "",
            "  ",
            "".join(
                random.choices(
                    string.ascii_letters + string.digits + string.punctuation,
                    k=18,
                ),
            ),
            re.sub(
                r"\A[A-Za-z0-9]{24,26}\.",
                f"{''.join(random.choices(string.ascii_letters + string.digits, k=2))}.",
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\A[A-Za-z0-9]{24,26}\.",
                f"{''.join(random.choices(string.ascii_letters + string.digits, k=50))}.",
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\A[A-Za-z0-9]{24,26}\.",
                (
                    f"{''.join(random.choices(string.ascii_letters + string.digits, k=12))}>{
                        ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                    }."
                ),
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\.[A-Za-z0-9]{6}\.",
                f".{''.join(random.choices(string.ascii_letters + string.digits, k=2))}.",
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\.[A-Za-z0-9]{6}\.",
                (f".{''.join(random.choices(string.ascii_letters + string.digits, k=50))}."),
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\.[A-Za-z0-9]{6}\.",
                (
                    f".{''.join(random.choices(string.ascii_letters + string.digits, k=3))}>{
                        ''.join(random.choices(string.ascii_letters + string.digits, k=2))
                    }."
                ),
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\.[A-Za-z0-9_-]{27,38}\Z",
                (
                    f".{
                        ''.join(
                            random.choices(string.ascii_letters + string.digits + '_-', k=2)
                        )
                    }"
                ),
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\.[A-Za-z0-9_-]{27,38}\Z",
                (
                    f".{
                        ''.join(
                            random.choices(string.ascii_letters + string.digits + '_-', k=50)
                        )
                    }"
                ),
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\.[A-Za-z0-9_-]{27,38}\Z",
                (
                    f".{
                        ''.join(
                            random.choices(string.ascii_letters + string.digits + '_-', k=16)
                        )
                    }>{
                        ''.join(
                            random.choices(string.ascii_letters + string.digits + '_-', k=16)
                        )
                    }"
                ),
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
        ),
        ids=[f"case_{i}" for i in range(13)],
    )
    def test_invalid_discord_bot_token(self, invalid_discord_bot_token: str) -> None:
        """Test that an error is raised when an invalid `DISCORD_BOT_TOKEN` is provided."""
        INVALID_DISCORD_BOT_TOKEN_MESSAGE: Final[str] = (
            "DISCORD_BOT_TOKEN must be a valid Discord bot token"  # noqa: S105
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("DISCORD_BOT_TOKEN"):
            os.environ["DISCORD_BOT_TOKEN"] = invalid_discord_bot_token

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_DISCORD_BOT_TOKEN_MESSAGE
            ):
                RuntimeSettings._setup_discord_bot_token()


class TestSetupDiscordLogChannelWebhookURL:
    """Test case to unit-test the `_setup_discord_log_channel_webhook()` function."""

    @pytest.mark.parametrize(
        "test_discord_log_channel_webhook_url",
        itertools.chain(
            RandomDiscordLogChannelWebhookURLGenerator.multiple_values(
                with_trailing_slash=False,
            ),
            RandomDiscordLogChannelWebhookURLGenerator.multiple_values(
                count=1,
                with_trailing_slash=True,
            ),
            (f"    {RandomDiscordLogChannelWebhookURLGenerator.single_value()}   ",),
        ),
        ids=[f"case_{i}" for i in range(7)],
    )
    def test_setup_discord_log_channel_webhook_successful(
        self,
        test_discord_log_channel_webhook_url: str,
    ) -> None:
        """
        Test that the given `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is used when provided.

        In this test, the provided `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is valid
        and so must be saved successfully.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("DISCORD_LOG_CHANNEL_WEBHOOK_URL"):
            os.environ["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = (
                test_discord_log_channel_webhook_url
            )

            RuntimeSettings._setup_discord_log_channel_webhook()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] == (
            test_discord_log_channel_webhook_url.strip()
        )

    def test_missing_discord_log_channel_webhook_url(self) -> None:
        """Test that no error occurs when no `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with (
            EnvVariableDeleter("DISCORD_LOG_CHANNEL_WEBHOOK_URL"),
            pytest.raises(
                expected_exception=ImproperlyConfiguredError,
                match=(
                    "DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL "
                    "that points to a discord channel where logs should be displayed."
                ),
            ),
        ):
            RuntimeSettings._setup_discord_log_channel_webhook()

    @pytest.mark.parametrize(
        "invalid_discord_log_channel_url",
        (
            "invalid_discord_log_channel_url",
            "",
            "  ",
            re.sub(
                r"/\d{17,20}/",
                (
                    f"/{''.join(random.choices(string.ascii_letters + string.digits, k=9))}>"
                    f"{''.join(random.choices(string.ascii_letters + string.digits, k=9))}/"
                ),
                string=RandomDiscordLogChannelWebhookURLGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"/[a-zA-Z\d]{60,90}",
                (
                    f"/{''.join(random.choices(string.ascii_letters + string.digits, k=37))}>"
                    f"{''.join(random.choices(string.ascii_letters + string.digits, k=37))}"
                ),
                string=RandomDiscordLogChannelWebhookURLGenerator.single_value(),
                count=1,
            ),
        ),
        ids=[f"case_{i}" for i in range(5)],
    )
    def test_invalid_discord_log_channel_webhook_url(
        self,
        invalid_discord_log_channel_url: str,
    ) -> None:
        """Test that an error occurs when the `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is invalid."""
        INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE: Final[str] = (
            "DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL "
            "that points to a discord channel where logs should be displayed."
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("DISCORD_LOG_CHANNEL_WEBHOOK_URL"):
            os.environ["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = invalid_discord_log_channel_url

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE,
            ):
                RuntimeSettings._setup_discord_log_channel_webhook()


class TestSetupDiscordGuildID:
    """Test case to unit-test the `_setup_discord_guild_id()` function."""

    @pytest.mark.parametrize(
        "test_discord_guild_id",
        itertools.chain(
            RandomDiscordGuildIDGenerator.multiple_values(),
            (f"    {RandomDiscordGuildIDGenerator.single_value()}   ",),
        ),
        ids=[f"case_{i}" for i in range(6)],
    )
    def test_setup_discord_guild_id_successful(self, test_discord_guild_id: str) -> None:
        """Test the given `_DISCORD_MAIN_GUILD_ID` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("DISCORD_GUILD_ID"):
            os.environ["DISCORD_GUILD_ID"] = test_discord_guild_id

            RuntimeSettings._setup_discord_guild_id()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["_DISCORD_MAIN_GUILD_ID"] == int(
            test_discord_guild_id.strip()
        )

    def test_missing_discord_guild_id(self) -> None:
        """Test that an error is raised when no `DISCORD_GUILD_ID` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with (
            EnvVariableDeleter("DISCORD_GUILD_ID"),
            pytest.raises(
                ImproperlyConfiguredError, match=r"DISCORD_GUILD_ID.*valid.*Discord guild ID"
            ),
        ):
            RuntimeSettings._setup_discord_guild_id()

    @pytest.mark.parametrize(
        "invalid_discord_guild_id",
        (
            "invalid_discord_guild_id",
            "",
            "  ",
            "".join(
                random.choices(
                    string.ascii_letters + string.digits + string.punctuation,
                    k=18,
                ),
            ),
            "".join(random.choices(string.digits, k=2)),
            "".join(random.choices(string.digits, k=50)),
        ),
        ids=[f"case_{i}" for i in range(6)],
    )
    def test_invalid_discord_guild_id(self, invalid_discord_guild_id: str) -> None:
        """Test that an error is raised when an invalid `DISCORD_GUILD_ID` is provided."""
        INVALID_DISCORD_GUILD_ID_MESSAGE: Final[str] = (
            "DISCORD_GUILD_ID must be a valid Discord guild ID"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("DISCORD_GUILD_ID"):
            os.environ["DISCORD_GUILD_ID"] = invalid_discord_guild_id

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_DISCORD_GUILD_ID_MESSAGE
            ):
                RuntimeSettings._setup_discord_guild_id()


class TestSetupGroupFullName:
    """Test case to unit-test the `_setup_group_full_name()` function."""

    @pytest.mark.parametrize(
        "test_group_full_name",
        (
            "Computer Science Society",
            "Arts & Crafts Soc",
            "3Bugs Fringe Theatre Society",
            "Burn FM.com",
            "Dental Society",
            "Devil's Advocate Society",
            "KASE: Knowledge And Skills Exchange",
            "Law for Non-Law",
            "   Computer Science Society    ",
            "Computer Science Society?",
            "Computer Science Society!",
        ),
    )
    def test_setup_group_full_name_successful(self, test_group_full_name: str) -> None:
        """Test that the given `GROUP_NAME` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("GROUP_NAME"):
            os.environ["GROUP_NAME"] = test_group_full_name

            RuntimeSettings._setup_group_full_name()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["_GROUP_FULL_NAME"] == test_group_full_name.strip().translate(
            {
                ord(unicode_char): ascii_char
                for unicode_char, ascii_char in zip("‘’´“”–-", "''`\"\"--", strict=True)  # noqa: RUF001
            },
        )

    def test_missing_group_full_name(self) -> None:
        """Test that no error occurs when no `GROUP_NAME` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("GROUP_NAME"):
            try:
                RuntimeSettings._setup_group_full_name()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert not RuntimeSettings()["_GROUP_FULL_NAME"]

    @pytest.mark.parametrize(
        "invalid_group_full_name",
        (
            "Computer Science$Society",
            "Computer Science£Society",
            "Computer Science*Society",
        ),
        ids=[f"case_{i}" for i in range(3)],
    )
    def test_invalid_group_full_name(self, invalid_group_full_name: str) -> None:
        """Test that an error is raised when an invalid `GROUP_NAME` is provided."""
        INVALID_GROUP_NAME_MESSAGE: Final[str] = (
            "GROUP_NAME must not contain any invalid characters"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("GROUP_NAME"):
            os.environ["GROUP_NAME"] = invalid_group_full_name

            with pytest.raises(ImproperlyConfiguredError, match=INVALID_GROUP_NAME_MESSAGE):
                RuntimeSettings._setup_group_full_name()


class TestSetupGroupShortName:
    """Test case to unit-test the `_setup_group_short_name()` function."""

    @pytest.mark.parametrize(
        "test_group_short_name",
        (
            "CSS",
            "ArtSoc",
            "3Bugs",
            "BurnFM.com",
            "L4N-L",
            "   CSS    ",
            "CSS?",
            "CSS!",
        ),
    )
    def test_setup_group_short_name_successful(self, test_group_short_name: str) -> None:
        """Test that the given `GROUP_SHORT_NAME` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("GROUP_SHORT_NAME"):
            os.environ["GROUP_SHORT_NAME"] = test_group_short_name

            RuntimeSettings._setup_group_short_name()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["_GROUP_SHORT_NAME"] == (
            test_group_short_name.strip().translate(
                {
                    ord(unicode_char): ascii_char
                    for unicode_char, ascii_char in zip("‘’´“”–-", "''`\"\"--", strict=True)  # noqa: RUF001
                },
            )
        )

    def test_missing_group_short_name_without_group_full_name(self) -> None:
        """Test that no error occurs when no `GROUP_SHORT_NAME` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("GROUP_SHORT_NAME"), EnvVariableDeleter("GROUP_NAME"):
            RuntimeSettings._setup_group_full_name()
            assert RuntimeSettings._settings["_GROUP_FULL_NAME"] is None

            try:
                RuntimeSettings._setup_group_short_name()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert not RuntimeSettings()["_GROUP_SHORT_NAME"]

    @pytest.mark.parametrize(
        "invalid_group_short_name",
        (
            "C S S",
            "CS$S",
            "CS£S",
        ),
        ids=[f"case_{i}" for i in range(3)],
    )
    def test_invalid_group_short_name(self, invalid_group_short_name: str) -> None:
        """Test that an error is raised when an invalid `GROUP_SHORT_NAME` is provided."""
        INVALID_GROUP_SHORT_NAME_MESSAGE: Final[str] = (
            "GROUP_SHORT_NAME must not contain any invalid characters"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("GROUP_SHORT_NAME"):
            os.environ["GROUP_SHORT_NAME"] = invalid_group_short_name

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_GROUP_SHORT_NAME_MESSAGE
            ):
                RuntimeSettings._setup_group_short_name()


class TestSetupPurchaseMembershipURL:
    """Test case to unit-test the `_setup_purchase_membership_url()` function."""

    @pytest.mark.parametrize(
        "test_purchase_membership_url",
        ("https://google.com", "www.google.com/", "    https://google.com   "),
    )
    def test_setup_purchase_membership_url_successful(
        self, test_purchase_membership_url: str
    ) -> None:
        """Test that the given valid `PURCHASE_MEMBERSHIP_URL` is used when one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("PURCHASE_MEMBERSHIP_URL"):
            os.environ["PURCHASE_MEMBERSHIP_URL"] = test_purchase_membership_url

            RuntimeSettings._setup_purchase_membership_url()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["PURCHASE_MEMBERSHIP_URL"] == (
            f"https://{test_purchase_membership_url.strip()}"
            if "://" not in test_purchase_membership_url
            else test_purchase_membership_url.strip()
        )

    def test_missing_purchase_membership_url(self) -> None:
        """Test that no error occurs when no `PURCHASE_MEMBERSHIP_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("PURCHASE_MEMBERSHIP_URL"):
            try:
                RuntimeSettings._setup_purchase_membership_url()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert not RuntimeSettings()["PURCHASE_MEMBERSHIP_URL"]

    @pytest.mark.parametrize(
        "invalid_purchase_membership_url",
        ("invalid_purchase_membership_url", "www.google..com/"),
    )
    def test_invalid_purchase_membership_url(
        self, invalid_purchase_membership_url: str
    ) -> None:
        """Test that an error occurs when the provided `PURCHASE_MEMBERSHIP_URL` is invalid."""
        INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE: Final[str] = (
            "PURCHASE_MEMBERSHIP_URL must be a valid URL"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("PURCHASE_MEMBERSHIP_URL"):
            os.environ["PURCHASE_MEMBERSHIP_URL"] = invalid_purchase_membership_url

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE
            ):
                RuntimeSettings._setup_purchase_membership_url()


class TestSetupMembershipPerksURL:
    """Test case to unit-test the `_setup_membership_perks_url()` function."""

    @pytest.mark.parametrize(
        "test_membership_perks_url",
        ("https://google.com", "www.google.com/", "    https://google.com   "),
    )
    def test_setup_membership_perks_url_successful(
        self, test_membership_perks_url: str
    ) -> None:
        """Test that the given valid `MEMBERSHIP_PERKS_URL` is used when one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MEMBERSHIP_PERKS_URL"):
            os.environ["MEMBERSHIP_PERKS_URL"] = test_membership_perks_url

            RuntimeSettings._setup_membership_perks_url()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["MEMBERSHIP_PERKS_URL"] == (
            f"https://{test_membership_perks_url.strip()}"
            if "://" not in test_membership_perks_url.strip()
            else test_membership_perks_url.strip()
        )

    def test_missing_membership_perks_url(self) -> None:
        """Test that no error occurs when no `MEMBERSHIP_PERKS_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MEMBERSHIP_PERKS_URL"):
            try:
                RuntimeSettings._setup_membership_perks_url()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert not RuntimeSettings()["MEMBERSHIP_PERKS_URL"]

    @pytest.mark.parametrize(
        "invalid_membership_perks_url",
        ("invalid_membership_perks_url", "www.google..com/"),
    )
    def test_invalid_membership_perks_url(self, invalid_membership_perks_url: str) -> None:
        """Test that an error occurs when the provided `MEMBERSHIP_PERKS_URL` is invalid."""
        INVALID_MEMBERSHIP_PERKS_URL_MESSAGE: Final[str] = (
            "MEMBERSHIP_PERKS_URL must be a valid URL"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MEMBERSHIP_PERKS_URL"):
            os.environ["MEMBERSHIP_PERKS_URL"] = invalid_membership_perks_url

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_MEMBERSHIP_PERKS_URL_MESSAGE
            ):
                RuntimeSettings._setup_membership_perks_url()


class TestSetupPingCommandEasterEggProbability:
    """Test case to unit-test the `_setup_ping_command_easter_egg_probability()` function."""

    @pytest.mark.parametrize(
        "test_ping_command_easter_egg_probability",
        ("1", "0", "0.5", "    0.5   "),
    )
    def test_setup_ping_command_easter_egg_probability_successful(
        self, test_ping_command_easter_egg_probability: str
    ) -> None:
        """
        Test that the given `PING_COMMAND_EASTER_EGG_PROBABILITY` is used when provided.

        In this test, the provided `PING_COMMAND_EASTER_EGG_PROBABILITY` is valid
        and so must be saved successfully.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("PING_COMMAND_EASTER_EGG_PROBABILITY"):
            os.environ["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
                test_ping_command_easter_egg_probability
            )

            RuntimeSettings._setup_ping_command_easter_egg_probability()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["PING_COMMAND_EASTER_EGG_PROBABILITY"] == 100 * float(
            test_ping_command_easter_egg_probability.strip(),
        )

    def test_default_ping_command_easter_egg_probability(self) -> None:
        """Test that a default value is used if no `PING_COMMAND_EASTER_EGG_PROBABILITY`."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("PING_COMMAND_EASTER_EGG_PROBABILITY"):
            try:
                RuntimeSettings._setup_ping_command_easter_egg_probability()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert isinstance(
            RuntimeSettings()["PING_COMMAND_EASTER_EGG_PROBABILITY"], float | int
        )
        assert 0 <= RuntimeSettings()["PING_COMMAND_EASTER_EGG_PROBABILITY"] <= 100

    @pytest.mark.parametrize(
        "invalid_ping_command_easter_egg_probability",
        ("invalid_ping_command_easter_egg_probability", "-5", "1.1", "5", "-0.01"),
    )
    def test_invalid_ping_command_easter_egg_probability(
        self, invalid_ping_command_easter_egg_probability: str
    ) -> None:
        """Test that errors when provided `PING_COMMAND_EASTER_EGG_PROBABILITY` is invalid."""
        INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE: Final[str] = (
            "PING_COMMAND_EASTER_EGG_PROBABILITY must be a float between & including 0 to 1."
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("PING_COMMAND_EASTER_EGG_PROBABILITY"):
            os.environ["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
                invalid_ping_command_easter_egg_probability
            )

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE,
            ):
                RuntimeSettings._setup_ping_command_easter_egg_probability()


class TestSetupMessagesFile:
    """Test case to unit-test all functions that use/relate to the messages JSON file."""

    @pytest.mark.parametrize(
        "raw_invalid_messages_file_path",
        ("messages.json.invalid", "  "),
    )
    def test_get_messages_dict_with_invalid_messages_file_path(
        self, raw_invalid_messages_file_path: str
    ) -> None:
        """Test that an error occurs when the provided `messages_file_path` is invalid."""
        INVALID_MESSAGES_FILE_PATH: Path = Path(raw_invalid_messages_file_path.strip())

        with FileTemporaryDeleter(INVALID_MESSAGES_FILE_PATH):
            INVALID_MESSAGES_FILE_PATH_MESSAGE: Final[str] = (
                "MESSAGES_FILE_PATH must be a path to a file that exists"
            )
            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_MESSAGES_FILE_PATH_MESSAGE
            ):
                Settings._get_messages_dict(raw_invalid_messages_file_path)

    @pytest.mark.parametrize("test_messages_dict", ({"welcome_messages": ["Welcome!"]},))
    def test_get_messages_dict_with_no_messages_file_path(
        self, test_messages_dict: "Mapping[str, object]"
    ) -> None:
        """Test that the default value is used when no `messages_file_path` is provided."""
        DEFAULT_MESSAGES_FILE_PATH: Path = config.PROJECT_ROOT / "messages.json"

        with FileTemporaryDeleter(DEFAULT_MESSAGES_FILE_PATH):
            default_messages_file: TextIO
            with DEFAULT_MESSAGES_FILE_PATH.open("w") as default_messages_file:
                json.dump(test_messages_dict, fp=default_messages_file)

            assert (
                Settings._get_messages_dict(raw_messages_file_path=None) == test_messages_dict
            )

            DEFAULT_MESSAGES_FILE_PATH.unlink()

    @pytest.mark.parametrize("test_messages_dict", ({"welcome_messages": ["Welcome!"]},))
    def test_get_messages_dict_successful(
        self, test_messages_dict: "Mapping[str, object]"
    ) -> None:
        """Test that the given path is used when a `messages_file_path` is provided."""
        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(test_messages_dict, fp=temporary_messages_file)

            temporary_messages_file.close()

            assert (
                Settings._get_messages_dict(
                    raw_messages_file_path=temporary_messages_file.name,
                )
                == test_messages_dict
            )

            assert (
                Settings._get_messages_dict(
                    raw_messages_file_path=f"  {temporary_messages_file.name}   ",
                )
                == test_messages_dict
            )

    @pytest.mark.parametrize(
        "invalid_messages_json",
        (
            '{"welcome_messages": ["Welcome!"}',
            "[]",
            '["Welcome!"]',
            '"Welcome!"',
            "99",
            "null",
            "true",
            "false",
        ),
    )
    def test_get_messages_dict_with_invalid_json(self, invalid_messages_json: str) -> None:
        """Test that an error is raised when the messages-file contains invalid JSON."""
        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            temporary_messages_file.write(invalid_messages_json)

            temporary_messages_file.close()

            INVALID_MESSAGES_JSON_MESSAGE: Final[str] = (
                "Messages JSON file must contain a JSON string"
            )
            with pytest.raises(ImproperlyConfiguredError, match=INVALID_MESSAGES_JSON_MESSAGE):
                Settings._get_messages_dict(
                    raw_messages_file_path=temporary_messages_file.name,
                )

    @pytest.mark.parametrize("test_messages_dict", ({"welcome_messages": ["Welcome!"]},))
    def test_setup_welcome_messages_successful_with_messages_file_path(
        self, test_messages_dict: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that correct welcome messages are loaded when `MESSAGES_FILE_PATH` is valid."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(test_messages_dict, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                RuntimeSettings._setup_welcome_messages()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["WELCOME_MESSAGES"] == set(
            test_messages_dict["welcome_messages"],
        )

    @pytest.mark.parametrize("test_messages_dict", ({"welcome_messages": ["Welcome!"]},))
    def test_setup_welcome_messages_successful_with_no_messages_file_path(
        self, test_messages_dict: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that correct welcome messages are loaded when no `MESSAGES_FILE_PATH` given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        DEFAULT_MESSAGES_FILE_PATH: Path = config.PROJECT_ROOT / "messages.json"

        with FileTemporaryDeleter(DEFAULT_MESSAGES_FILE_PATH):
            default_messages_file: TextIO
            with DEFAULT_MESSAGES_FILE_PATH.open("w") as default_messages_file:
                json.dump(test_messages_dict, fp=default_messages_file)

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                RuntimeSettings._setup_welcome_messages()

            DEFAULT_MESSAGES_FILE_PATH.unlink()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["WELCOME_MESSAGES"] == set(
            test_messages_dict["welcome_messages"],
        )

    @pytest.mark.parametrize("no_welcome_messages_dict", ({"other_messages": ["Welcome!"]},))
    def test_welcome_messages_key_not_in_messages_json(
        self, no_welcome_messages_dict: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that error is raised when messages-file not contain `welcome_messages` key."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(no_welcome_messages_dict, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                exc_info: ExceptionInfo[MessagesJSONFileMissingKeyError]
                with pytest.raises(MessagesJSONFileMissingKeyError) as exc_info:
                    RuntimeSettings._setup_welcome_messages()

        assert exc_info.value.missing_key == "welcome_messages"

    @pytest.mark.parametrize(
        "invalid_welcome_messages_dict",
        (
            {"welcome_messages": {}},
            {"welcome_messages": []},
            {"welcome_messages": ""},
            {"welcome_messages": 99},
            {"welcome_messages": None},
            {"welcome_messages": True},
            {"welcome_messages": False},
        ),
    )
    def test_invalid_welcome_messages(
        self, invalid_welcome_messages_dict: "Mapping[str, object]"
    ) -> None:
        """Test that error is raised when the `welcome_messages` is not a valid value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(invalid_welcome_messages_dict, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                exc_info: ExceptionInfo[MessagesJSONFileValueError]
                with pytest.raises(MessagesJSONFileValueError) as exc_info:
                    RuntimeSettings._setup_welcome_messages()

        assert exc_info.value.dict_key == "welcome_messages"
        assert (
            exc_info.value.invalid_value == invalid_welcome_messages_dict["welcome_messages"]
        )

    @pytest.mark.parametrize("test_messages_dict", ({"roles_messages": ["Gaming"]},))
    def test_setup_roles_messages_successful_with_messages_file_path(
        self, test_messages_dict: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that correct roles messages are loaded when `MESSAGES_FILE_PATH` is valid."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(test_messages_dict, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                RuntimeSettings._setup_roles_messages()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["ROLES_MESSAGES"] == set(
            test_messages_dict["roles_messages"],
        )

    @pytest.mark.parametrize("test_messages_dict", ({"roles_messages": ["Gaming"]},))
    def test_setup_roles_messages_successful_with_no_messages_file_path(
        self, test_messages_dict: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that correct roles messages are loaded when no `MESSAGES_FILE_PATH` given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        DEFAULT_MESSAGES_FILE_PATH: Path = config.PROJECT_ROOT / "messages.json"

        with FileTemporaryDeleter(DEFAULT_MESSAGES_FILE_PATH):
            default_messages_file: TextIO
            with DEFAULT_MESSAGES_FILE_PATH.open("w") as default_messages_file:
                json.dump(test_messages_dict, fp=default_messages_file)

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                RuntimeSettings._setup_roles_messages()

            DEFAULT_MESSAGES_FILE_PATH.unlink()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["ROLES_MESSAGES"] == set(
            test_messages_dict["roles_messages"],
        )

    @pytest.mark.parametrize("no_roles_messages_dict", ({"other_messages": ["Gaming"]},))
    def test_roles_messages_key_not_in_messages_json(
        self, no_roles_messages_dict: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that error is raised when messages-file not contain `roles_messages` key."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(no_roles_messages_dict, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                exc_info: ExceptionInfo[MessagesJSONFileMissingKeyError]
                with pytest.raises(MessagesJSONFileMissingKeyError) as exc_info:
                    RuntimeSettings._setup_roles_messages()

        assert exc_info.value.missing_key == "roles_messages"

    @pytest.mark.parametrize(
        "invalid_roles_messages_dict",
        (
            {"roles_messages": {}},
            {"roles_messages": []},
            {"roles_messages": ""},
            {"roles_messages": 99},
            {"roles_messages": None},
            {"roles_messages": True},
            {"roles_messages": False},
        ),
    )
    def test_invalid_roles_messages(
        self, invalid_roles_messages_dict: "Mapping[str, object]"
    ) -> None:
        """Test that error is raised when the `roles_messages` is not a valid value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(invalid_roles_messages_dict, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                exc_info: ExceptionInfo[MessagesJSONFileValueError]
                with pytest.raises(MessagesJSONFileValueError) as exc_info:
                    RuntimeSettings._setup_roles_messages()

        assert exc_info.value.dict_key == "roles_messages"
        assert exc_info.value.invalid_value == invalid_roles_messages_dict["roles_messages"]


class TestSetupMembersListURLSessionCookie:
    """Test case to unit-test the `_setup_members_list_auth_session_cookie()` function."""

    @pytest.mark.parametrize(
        "test_members_list_url_session_cookie",
        (
            "".join(random.choices(string.hexdigits, k=random.randint(128, 256))),
            f"  {''.join(random.choices(string.hexdigits, k=random.randint(128, 256)))}   ",
        ),
        ids=[f"case_{i}" for i in range(2)],
    )
    def test_setup_members_list_auth_session_cookie_successful(
        self, test_members_list_url_session_cookie: str
    ) -> None:
        """
        Test that the given `test_members_list_url_session_cookie` is used when provided.

        In this test, the provided `test_members_list_url_session_cookie` is valid
        and so must be saved successfully.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MEMBERS_LIST_URL_SESSION_COOKIE"):
            os.environ["MEMBERS_LIST_URL_SESSION_COOKIE"] = (
                test_members_list_url_session_cookie
            )

            RuntimeSettings._setup_members_list_auth_session_cookie()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["MEMBERS_LIST_AUTH_SESSION_COOKIE"] == (
            test_members_list_url_session_cookie.strip()
        )

    def test_missing_members_list_url_session_cookie(self) -> None:
        """Test that an error is raised when no `MEMBERS_LIST_URL_SESSION_COOKIE` is given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MEMBERS_LIST_URL_SESSION_COOKIE"):  # noqa: SIM117
            with pytest.raises(
                ImproperlyConfiguredError,
                match=r"MEMBERS_LIST_URL_SESSION_COOKIE.*valid.*\.ASPXAUTH cookie",
            ):
                RuntimeSettings._setup_members_list_auth_session_cookie()

    @pytest.mark.parametrize(
        "invalid_members_list_url_session_cookie",
        (
            "invalid_members_list_url_session_cookie",
            "",
            "  ",
            "".join(random.choices(string.hexdigits, k=5)),
            "".join(random.choices(string.hexdigits, k=500)),
            (
                f"{''.join(random.choices(string.hexdigits, k=64))}>{
                    ''.join(random.choices(string.hexdigits, k=64))
                }"
            ),
        ),
        ids=[f"case_{i}" for i in range(6)],
    )
    def test_invalid_members_list_url_session_cookie(
        self, invalid_members_list_url_session_cookie: str
    ) -> None:
        """Test that an error occurs when `MEMBERS_LIST_URL_SESSION_COOKIE` is invalid."""
        INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE: Final[str] = (
            "MEMBERS_LIST_URL_SESSION_COOKIE must be a valid .ASPXAUTH cookie"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MEMBERS_LIST_URL_SESSION_COOKIE"):
            os.environ["MEMBERS_LIST_URL_SESSION_COOKIE"] = (
                invalid_members_list_url_session_cookie
            )

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE,
            ):
                RuntimeSettings._setup_members_list_auth_session_cookie()


class TestSetupSendIntroductionReminders:
    """Test case to unit-test the configuration for sending introduction reminders."""

    @pytest.mark.parametrize(
        "test_send_introduction_reminders_value",
        list(
            set(
                itertools.chain(
                    config.VALID_SEND_INTRODUCTION_REMINDERS_VALUES,
                    (
                        f"  {
                            next(
                                iter(
                                    value
                                    for value in config.VALID_SEND_INTRODUCTION_REMINDERS_VALUES
                                    if value.isalpha()
                                )
                            )
                        }   ",  # noqa: E501
                        next(
                            iter(
                                value
                                for value in config.VALID_SEND_INTRODUCTION_REMINDERS_VALUES
                                if value.isalpha()
                            ),
                        ).lower(),
                        next(
                            iter(
                                value
                                for value in config.VALID_SEND_INTRODUCTION_REMINDERS_VALUES
                                if value.isalpha()
                            ),
                        ).upper(),
                        "".join(
                            random.choice((str.upper, str.lower))(character)
                            for character in next(
                                iter(
                                    value
                                    for value in config.VALID_SEND_INTRODUCTION_REMINDERS_VALUES  # noqa: E501
                                    if value.isalpha()
                                ),
                            )
                        ),
                    ),
                ),
            )
        )[:14],
        ids=[f"case_{i}" for i in range(14)],
    )
    def test_setup_send_introduction_reminders_successful(
        self, test_send_introduction_reminders_value: str
    ) -> None:
        """Test that setup is successful when a valid option is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
            os.environ["SEND_INTRODUCTION_REMINDERS"] = test_send_introduction_reminders_value

            RuntimeSettings._setup_send_introduction_reminders()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["SEND_INTRODUCTION_REMINDERS"] == (
            "once"
            if test_send_introduction_reminders_value.lower().strip() in config.TRUE_VALUES
            else (
                False
                if test_send_introduction_reminders_value.lower().strip()
                not in (
                    "once",
                    "interval",
                )
                else test_send_introduction_reminders_value.lower().strip()
            )
        )

    def test_default_send_introduction_reminders_value(self) -> None:
        """Test that a default value is used when no introduction-reminders-flag is given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
            try:
                RuntimeSettings._setup_send_introduction_reminders()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["SEND_INTRODUCTION_REMINDERS"] in ("once", "interval", False)

    @pytest.mark.parametrize(
        "invalid_send_introduction_reminders_value",
        (
            "invalid_send_introduction_reminders_value",
            "",
            "  ",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=8),
            ),
        ),
        ids=[f"case_{i}" for i in range(4)],
    )
    def test_invalid_send_introduction_reminders(
        self, invalid_send_introduction_reminders_value: str
    ) -> None:
        """Test that an error occurs when an invalid introduction-reminders-flag is given."""
        INVALID_SEND_INTRODUCTION_REMINDERS_VALUE_MESSAGE: Final[str] = (
            'SEND_INTRODUCTION_REMINDERS must be one of: "Once", "Interval" or "False"'
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
            os.environ["SEND_INTRODUCTION_REMINDERS"] = (
                invalid_send_introduction_reminders_value
            )

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_SEND_INTRODUCTION_REMINDERS_VALUE_MESSAGE,
            ):
                RuntimeSettings._setup_send_introduction_reminders()

    @pytest.mark.parametrize(
        "test_send_introduction_reminders_interval",
        (
            f"{random.randint(3, 999)}s",
            f"{random.randint(3, 999)}.{random.randint(0, 999)}s",
            (
                f"  {random.randint(3, 999)}{
                    random.choice(('', f'.{random.randint(0, 999)}'))
                }s   "
            ),
            f"{random.randint(1, 999)}{random.choice(('', f'.{random.randint(0, 999)}'))}m",
            f"{random.randint(1, 999)}{random.choice(('', f'.{random.randint(0, 999)}'))}h",
            (
                f"{random.randint(3, 999)}{random.choice(('', f'.{random.randint(0, 999)}'))}s{
                    random.randint(0, 999)
                }{random.choice(('', f'.{random.randint(0, 999)}'))}m{random.randint(0, 999)}{
                    random.choice(('', f'.{random.randint(0, 999)}'))
                }h"
            ),
            (
                f"{random.randint(3, 999)}{
                    random.choice(('', f'.{random.randint(0, 999)}'))
                } s  {random.randint(0, 999)}{
                    random.choice(('', f'.{random.randint(0, 999)}'))
                }   m   {random.randint(0, 999)}{
                    random.choice(('', f'.{random.randint(0, 999)}'))
                }  h"
            ),
        ),
        ids=[f"case_{i}" for i in range(7)],
    )
    def test_setup_send_introduction_reminders_interval_successful(
        self, test_send_introduction_reminders_interval: str
    ) -> None:
        """
        Test that the given `SEND_INTRODUCTION_REMINDERS_INTERVAL` is used when provided.

        In this test, the provided `SEND_INTRODUCTION_REMINDERS_INTERVAL` is valid
        and so must be saved successfully.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._setup_send_introduction_reminders()

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                test_send_introduction_reminders_interval
            )

            RuntimeSettings._setup_send_introduction_reminders_interval()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"] == {
            key: float(value)
            for key, value in (
                re.match(
                    r"\A(?:(?P<seconds>(?:\d*\.)?\d+)\s*s)?\s*(?:(?P<minutes>(?:\d*\.)?\d+)\s*m)?\s*(?:(?P<hours>(?:\d*\.)?\d+)\s*h)?\Z",
                    test_send_introduction_reminders_interval.lower().strip(),
                )
                .groupdict()  # type: ignore[union-attr]
                .items()
            )
            if value
        }

        assert (
            "seconds" in RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"]
            or "minutes" in RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"]
            or "hours" in RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"]
        )

        assert all(
            isinstance(value, float)
            for value in RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"].values()
        )

        timedelta_error: TypeError
        try:
            assert timedelta(
                **RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"]
            ) > timedelta(seconds=3)

        except TypeError as timedelta_error:
            if "invalid keyword argument for __new__()" not in str(timedelta_error):
                raise timedelta_error from timedelta_error

            pytest.fail(
                (
                    "Failed to construct `timedelta` object "
                    "from given `SEND_INTRODUCTION_REMINDERS_INTERVAL`"
                ),
                pytrace=False,
            )

    def test_default_send_introduction_reminders_interval(self) -> None:
        """Test that a default value is used when no `SEND_INTRODUCTION_REMINDERS_INTERVAL`."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._setup_send_introduction_reminders()

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            try:
                RuntimeSettings._setup_send_introduction_reminders_interval()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert (
            "seconds" in RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"]
            or "minutes" in RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"]
            or "hours" in RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"]
        )

        assert all(
            isinstance(value, float | int)
            for value in RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"].values()
        )

        timedelta_error: TypeError
        try:
            assert timedelta(
                **RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"]
            ) > timedelta(seconds=3)

        except TypeError as timedelta_error:
            if "invalid keyword argument for __new__()" not in str(timedelta_error):
                raise timedelta_error from timedelta_error

            pytest.fail(
                (
                    "Failed to construct `timedelta` object "
                    "from given `SEND_INTRODUCTION_REMINDERS_INTERVAL`"
                ),
                pytrace=False,
            )

    def test_setup_send_introduction_reminders_interval_without_send_introduction_reminders_setup(  # noqa: E501
        self,
    ) -> None:
        """Test that an error is raised when setting up the interval without the flag."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        RuntimeSettings._settings.pop("SEND_INTRODUCTION_REMINDERS", None)

        with pytest.raises(RuntimeError, match="Invalid setup order"):
            RuntimeSettings._setup_send_introduction_reminders_interval()

    @pytest.mark.parametrize(
        "invalid_send_introduction_reminders_interval",
        (
            "invalid_send_introduction_reminders_interval",
            "",
            "  ",
            f"{random.randint(1, 999)}d",
            f"{random.randint(3, 999)},{random.randint(0, 999)}s",
        ),
        ids=[f"case_{i}" for i in range(5)],
    )
    def test_invalid_send_introduction_reminders_interval_flag_disabled(
        self, invalid_send_introduction_reminders_interval: str
    ) -> None:
        """
        Test that no error is raised when `SEND_INTRODUCTION_REMINDERS_INTERVAL` is invalid.

        The enable/disable flag `SEND_INTRODUCTION_REMINDERS` is disabled (set to `False`)
        during this test, so an invalid interval value should be ignored.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                invalid_send_introduction_reminders_interval
            )

            with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
                os.environ["SEND_INTRODUCTION_REMINDERS"] = "false"
                RuntimeSettings._setup_send_introduction_reminders()

                try:
                    RuntimeSettings._setup_send_introduction_reminders_interval()
                except ImproperlyConfiguredError:
                    pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

    @pytest.mark.parametrize(
        "invalid_send_introduction_reminders_interval",
        (
            "invalid_send_introduction_reminders_interval",
            f"{random.randint(1, 999)}d",
            f"{random.randint(3, 999)},{random.randint(0, 999)}s",
        ),
        ids=[f"case_{i}" for i in range(3)],
    )
    def test_invalid_send_introduction_reminders_interval_flag_enabled(
        self,
        invalid_send_introduction_reminders_interval: str,
    ) -> None:
        """
        Test that an error is raised when `SEND_INTRODUCTION_REMINDERS_INTERVAL` is invalid.

        The enable/disable flag `SEND_INTRODUCTION_REMINDERS` is enabled
        (set to `once` or `interval`) during this test,
        so an invalid interval value should not be ignored, and an error should be raised.
        """
        INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
            "SEND_INTRODUCTION_REMINDERS_INTERVAL must contain the interval "
            "in any combination of seconds, minutes or hours"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                invalid_send_introduction_reminders_interval
            )

            with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
                os.environ["SEND_INTRODUCTION_REMINDERS"] = random.choice(("once", "interval"))
                RuntimeSettings._setup_send_introduction_reminders()

                with pytest.raises(
                    ImproperlyConfiguredError,
                    match=INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE,
                ):
                    RuntimeSettings._setup_send_introduction_reminders_interval()

    @pytest.mark.parametrize(
        "too_small_send_introduction_reminders",
        ("0.5s", "0s", "0.03m", "0m", "0.0005h", "0h"),
    )
    def test_too_small_send_introduction_reminders_interval_flag_disabled(
        self, too_small_send_introduction_reminders: str
    ) -> None:
        """
        Test that no error is raised when `SEND_INTRODUCTION_REMINDERS_INTERVAL` is too small.

        The enable/disable flag `SEND_INTRODUCTION_REMINDERS` is disabled (set to `False`)
        during this test, so an invalid interval value should be ignored.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                too_small_send_introduction_reminders
            )

            with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
                os.environ["SEND_INTRODUCTION_REMINDERS"] = "false"
                RuntimeSettings._setup_send_introduction_reminders()

                try:
                    RuntimeSettings._setup_send_introduction_reminders_interval()
                except ImproperlyConfiguredError:
                    pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

    @pytest.mark.parametrize(
        "too_small_send_introduction_reminders",
        ("0.5s", "0s", "0.03m", "0m", "0.0005h", "0h"),
    )
    def test_too_small_send_introduction_reminders_interval_flag_enabled(
        self,
        too_small_send_introduction_reminders: str,
    ) -> None:
        """
        Test that an error is raised when `SEND_INTRODUCTION_REMINDERS_INTERVAL` is too small.

        The enable/disable flag `SEND_INTRODUCTION_REMINDERS` is enabled
        (set to `once` or `interval`) during this test,
        so an invalid interval value should not be ignored, and an error should be raised.
        """
        TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
            "SEND_INTRODUCTION_REMINDERS_INTERVAL must be longer than 3 seconds."
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                too_small_send_introduction_reminders
            )

            with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
                os.environ["SEND_INTRODUCTION_REMINDERS"] = random.choice(("once", "interval"))
                RuntimeSettings._setup_send_introduction_reminders()

                with pytest.raises(
                    ImproperlyConfiguredError,
                    match=TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE,
                ):
                    RuntimeSettings._setup_send_introduction_reminders_interval()


class TestSetupSendGetRolesReminders:
    """Test case to unit-test the configuration for sending get-roles reminders."""

    @pytest.mark.parametrize(
        "test_send_get_roles_reminder_value",
        list(
            set(
                itertools.chain(
                    config.TRUE_VALUES | config.FALSE_VALUES,
                    (
                        f"  {
                            next(
                                iter(
                                    value
                                    for value in config.TRUE_VALUES | config.FALSE_VALUES
                                    if value.isalpha()
                                )
                            )
                        }   ",
                        next(
                            iter(
                                value
                                for value in config.TRUE_VALUES | config.FALSE_VALUES
                                if value.isalpha()
                            ),
                        ).lower(),
                        next(
                            iter(
                                value
                                for value in config.TRUE_VALUES | config.FALSE_VALUES
                                if value.isalpha()
                            ),
                        ).upper(),
                        "".join(
                            random.choice((str.upper, str.lower))(character)
                            for character in next(
                                iter(
                                    value
                                    for value in config.TRUE_VALUES | config.FALSE_VALUES
                                    if value.isalpha()
                                ),
                            )
                        ),
                    ),
                ),
            )
        )[:14],
        ids=[f"case_{i}" for i in range(14)],
    )
    def test_setup_send_get_roles_reminders_successful(
        self, test_send_get_roles_reminder_value: str
    ) -> None:
        """Test that setup is successful when a valid option is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS"):
            os.environ["SEND_GET_ROLES_REMINDERS"] = test_send_get_roles_reminder_value

            RuntimeSettings._setup_send_get_roles_reminders()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["SEND_GET_ROLES_REMINDERS"] == (
            test_send_get_roles_reminder_value.lower().strip() in config.TRUE_VALUES
        )

    def test_default_send_get_roles_reminders_value(self) -> None:
        """Test that a default value is used when no get-roles-reminders-flag is given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS"):
            try:
                RuntimeSettings._setup_send_get_roles_reminders()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["SEND_GET_ROLES_REMINDERS"] in (True, False)

    @pytest.mark.parametrize(
        "invalid_send_get_role_reminders_value",
        (
            "invalid_send_get_role_reminders_value",
            "",
            "  ",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=8),
            ),
        ),
        ids=[f"case_{i}" for i in range(4)],
    )
    def test_invalid_send_get_roles_reminders(
        self, invalid_send_get_role_reminders_value: str
    ) -> None:
        """Test that an error occurs when an invalid get-roles-reminders-flag is given."""
        INVALID_SEND_GET_ROLES_REMINDERS_VALUE_MESSAGE: Final[str] = (
            "SEND_GET_ROLES_REMINDERS must be a boolean value"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS"):
            os.environ["SEND_GET_ROLES_REMINDERS"] = invalid_send_get_role_reminders_value

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_SEND_GET_ROLES_REMINDERS_VALUE_MESSAGE
            ):
                RuntimeSettings._setup_send_get_roles_reminders()


class TestSetupSendGetRolesRemindersInterval:
    """Test case to unit-test the `_setup_advanced_send_get_roles_reminders_interval()` function."""  # noqa: E501, W505

    def test_setup_interval_without_send_roles_reminders_setup(self) -> None:
        """Test that an error is raised when setting up the interval without the flag."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
            "Invalid setup order: SEND_GET_ROLES_REMINDERS must be set up "
            "before ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL can be set up."
        )

        with (
            EnvVariableDeleter("SEND_GET_ROLES_REMINDERS_INTERVAL"),
            EnvVariableDeleter("SEND_GET_ROLES_REMINDERS"),
            pytest.raises(RuntimeError, match=INVALID_SETUP_ORDER_MESSAGE),
        ):
            RuntimeSettings._setup_advanced_send_get_roles_reminders_interval()

    def test_default_send_get_roles_reminders_interval(self) -> None:
        """Test that a default value is used when no `SEND_GET_ROLES_REMINDERS_INTERVAL`."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._setup_send_get_roles_reminders()

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS_INTERVAL"):
            try:
                RuntimeSettings._setup_advanced_send_get_roles_reminders_interval()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL"] == {"hours": 24}

    @pytest.mark.parametrize(
        "test_invalid_send_get_roles_reminders_interval",
        ("obviously not a valid interval", "3.5", "3.5f", "3.5a"),
    )
    def test_invalid_send_get_roles_reminders_interval(
        self, test_invalid_send_get_roles_reminders_interval: str
    ) -> None:
        """Test that an error is raised when an invalid interval is provided."""
        INVALID_SEND_GET_ROLES_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
            "ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL must contain the interval "
            "in any combination of seconds, minutes or hours"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        os.environ["SEND_GET_ROLES_REMINDERS"] = "True"

        RuntimeSettings._setup_send_get_roles_reminders()

        with EnvVariableDeleter("ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL"):
            os.environ["ADVANCED_SEND_GET_ROLES_REMINDERS_INTERVAL"] = (
                test_invalid_send_get_roles_reminders_interval
            )

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_SEND_GET_ROLES_REMINDERS_INTERVAL_MESSAGE,
            ):
                RuntimeSettings._setup_advanced_send_get_roles_reminders_interval()


class TestSetupSendGetRolesRemindersDelay:
    """Test case to unit-test the `_setup_advanced_send_get_roles_reminders_delay()` function."""  # noqa: E501, W505

    def test_setup_delay_without_send_roles_reminders_setup(self) -> None:
        """Test that an error is raised when setting up the delay without the flag."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
            "Invalid setup order: SEND_GET_ROLES_REMINDERS must be set up "
            "before SEND_GET_ROLES_REMINDERS_DELAY can be set up."
        )

        with (
            EnvVariableDeleter("SEND_GET_ROLES_REMINDERS_INTERVAL"),
            EnvVariableDeleter("SEND_GET_ROLES_REMINDERS"),
            pytest.raises(RuntimeError, match=INVALID_SETUP_ORDER_MESSAGE),
        ):
            RuntimeSettings._setup_send_get_roles_reminders_delay()

    def test_default_send_get_roles_reminders_delay(self) -> None:
        """Test that a default value is used when no `SEND_GET_ROLES_REMINDERS_DELAY`."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._setup_send_get_roles_reminders()

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS_DELAY"):
            try:
                RuntimeSettings._setup_send_get_roles_reminders_delay()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["SEND_GET_ROLES_REMINDERS_DELAY"] == timedelta(hours=40)

    @pytest.mark.parametrize(
        "too_short_get_roles_reminders_delay",
        ("0.5s", "0s", "0.03m", "0m", "0.0005h", "0h", "0.9d"),
    )
    def test_too_short_send_get_roles_reminders_delay(
        self, too_short_get_roles_reminders_delay: str
    ) -> None:
        """Test that an error is thrown if `SEND_GET_ROLES_REMINDERS_DELAY` is too short."""
        TOO_SMALL_SEND_GET_ROLES_REMINDERS_DELAY_MESSAGE: Final[str] = (
            "SEND_SEND_GET_ROLES_REMINDERS_DELAY must be longer than or equal to 1 day."
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        RuntimeSettings._setup_send_get_roles_reminders()

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS_DELAY"):
            os.environ["SEND_GET_ROLES_REMINDERS_DELAY"] = too_short_get_roles_reminders_delay

            with pytest.raises(
                ImproperlyConfiguredError,
                match=TOO_SMALL_SEND_GET_ROLES_REMINDERS_DELAY_MESSAGE,
            ):
                RuntimeSettings._setup_send_get_roles_reminders_delay()

    @pytest.mark.parametrize(
        "invalid_send_get_roles_reminders_delay",
        ("invalid_send_get_roles_reminders_delay", "3.5", "3.5f", "3.5a"),
    )
    def test_invalid_send_get_roles_reminders_delay(
        self, invalid_send_get_roles_reminders_delay: str
    ) -> None:
        """Test that an error is raised when an invalid delay is provided."""
        INVALID_SEND_GET_ROLES_REMINDERS_DELAY_MESSAGE: Final[str] = (
            "SEND_GET_ROLES_REMINDERS_DELAY must contain the delay "
            "in any combination of seconds, minutes, hours, days or weeks."
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        RuntimeSettings._setup_send_get_roles_reminders()

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS_DELAY"):
            os.environ["SEND_GET_ROLES_REMINDERS_DELAY"] = (
                invalid_send_get_roles_reminders_delay
            )

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_SEND_GET_ROLES_REMINDERS_DELAY_MESSAGE
            ):
                RuntimeSettings._setup_send_get_roles_reminders_delay()


class TestSetupStatisticsDays:
    """Test case to unit-test the `_setup_statistics_days()` function."""

    @pytest.mark.parametrize("test_statistics_days", ("5", "3.55", "664", "    5   "))
    def test_setup_statistics_days_successful(self, test_statistics_days: str) -> None:
        """Test that the given valid `STATISTICS_DAYS` is used when one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("STATISTICS_DAYS"):
            os.environ["STATISTICS_DAYS"] = test_statistics_days

            RuntimeSettings._setup_statistics_days()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["STATISTICS_DAYS"] == timedelta(
            days=float(test_statistics_days.strip()),
        )

    def test_default_statistics_days(self) -> None:
        """Test that a default value is used when no `STATISTICS_DAYS` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("STATISTICS_DAYS"):
            try:
                RuntimeSettings._setup_statistics_days()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert isinstance(RuntimeSettings()["STATISTICS_DAYS"], timedelta)

        assert RuntimeSettings()["STATISTICS_DAYS"] > timedelta(days=1)

    @pytest.mark.parametrize(
        "invalid_statistics_days",
        (
            "invalid_statistics_days",
            "",
            "  ",
            "".join(
                random.choices(
                    string.ascii_letters + string.digits + string.punctuation,
                    k=18,
                ),
            ),
        ),
        ids=[f"case_{i}" for i in range(4)],
    )
    def test_invalid_statistics_days(self, invalid_statistics_days: str) -> None:
        """Test that an error is raised when an invalid `STATISTICS_DAYS` is provided."""
        INVALID_STATISTICS_DAYS_MESSAGE: Final[str] = (
            "STATISTICS_DAYS must contain the statistics period in days"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("STATISTICS_DAYS"):
            os.environ["STATISTICS_DAYS"] = invalid_statistics_days

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_STATISTICS_DAYS_MESSAGE
            ):
                RuntimeSettings._setup_statistics_days()

    @pytest.mark.parametrize(
        "too_small_statistics_days",
        ("-15", "-2.3", "-0.02", "0", "0.40"),
    )
    def test_too_small_statistics_days(self, too_small_statistics_days: str) -> None:
        """Test that an error is raised when a too small `STATISTICS_DAYS` is provided."""
        TOO_SMALL_STATISTICS_DAYS_MESSAGE: Final[str] = (
            "STATISTICS_DAYS cannot be less than or equal to 1 day"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("STATISTICS_DAYS"):
            os.environ["STATISTICS_DAYS"] = too_small_statistics_days

            with pytest.raises(
                ImproperlyConfiguredError, match=TOO_SMALL_STATISTICS_DAYS_MESSAGE
            ):
                RuntimeSettings._setup_statistics_days()


class TestSetupStatisticsRoles:
    """Test case to unit-test the `_setup_statistics_roles()` function."""

    @pytest.mark.parametrize(
        "test_statistics_roles",
        (
            "Guest",
            "Guest,Member",
            "Guest,Member,Admin",
            "    Guest,Member,Admin   ",
            "    Guest ,   Member  ,Admin   ",
        ),
    )
    def test_setup_statistics_roles_successful(self, test_statistics_roles: str) -> None:
        """Test that the given valid `STATISTICS_ROLES` is used when they are provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("STATISTICS_ROLES"):
            os.environ["STATISTICS_ROLES"] = test_statistics_roles

            RuntimeSettings._setup_statistics_roles()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["STATISTICS_ROLES"] == {
            test_statistics_role.strip()
            for test_statistics_role in test_statistics_roles.strip().split(",")
            if test_statistics_role.strip()
        }

    def test_default_statistics_roles(self) -> None:
        """Test that default values are used when no `STATISTICS_ROLES` are provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("STATISTICS_ROLES"):
            try:
                RuntimeSettings._setup_statistics_roles()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert isinstance(RuntimeSettings()["STATISTICS_ROLES"], Iterable)

        assert bool(RuntimeSettings()["STATISTICS_ROLES"])

        assert all(
            isinstance(statistics_role, str) and bool(statistics_role)
            for statistics_role in RuntimeSettings()["STATISTICS_ROLES"]
        )


class TestSetupModerationDocumentURL:
    """Test case to unit-test the `_setup_moderation_document_url()` function."""

    @pytest.mark.parametrize(
        "test_moderation_document_url",
        ("https://google.com", "www.google.com/", "    https://google.com   "),
    )
    def test_setup_moderation_document_url_successful(
        self, test_moderation_document_url: str
    ) -> None:
        """Test that the given valid `MODERATION_DOCUMENT_URL` is used when one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MODERATION_DOCUMENT_URL"):
            os.environ["MODERATION_DOCUMENT_URL"] = test_moderation_document_url

            RuntimeSettings._setup_moderation_document_url()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["MODERATION_DOCUMENT_URL"] == (
            f"https://{test_moderation_document_url.strip()}"
            if "://" not in test_moderation_document_url.strip()
            else test_moderation_document_url.strip()
        )

    def test_missing_moderation_document_url(self) -> None:
        """Test that an error is raised when no `MODERATION_DOCUMENT_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MODERATION_DOCUMENT_URL"):  # noqa: SIM117
            with pytest.raises(
                ImproperlyConfiguredError, match=r"MODERATION_DOCUMENT_URL.*valid.*URL"
            ):
                RuntimeSettings._setup_moderation_document_url()

    @pytest.mark.parametrize(
        "invalid_moderation_document_url",
        ("invalid_moderation_document_url", "www.google..com/", "", "  "),
    )
    def test_invalid_moderation_document_url(
        self, invalid_moderation_document_url: str
    ) -> None:
        """Test that an error occurs when the provided `MODERATION_DOCUMENT_URL` is invalid."""
        INVALID_MODERATION_DOCUMENT_URL_MESSAGE: Final[str] = (
            "MODERATION_DOCUMENT_URL must be a valid URL"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MODERATION_DOCUMENT_URL"):
            os.environ["MODERATION_DOCUMENT_URL"] = invalid_moderation_document_url

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_MODERATION_DOCUMENT_URL_MESSAGE
            ):
                RuntimeSettings._setup_moderation_document_url()


class TestSetupManualModerationWarningMessageLocation:
    """Test case for the `_setup_strike_performed_manually_warning_location()` function."""

    @pytest.mark.parametrize(
        "test_manual_moderation_warning_message_location",
        ("DM", "dm", "general", "Memes", "   general  ", "JUST-CHATTING", "Talking4"),
    )
    def test_setup_strike_performed_manually_warning_location_successful(
        self, test_manual_moderation_warning_message_location: str
    ) -> None:
        """Test that the given valid `MANUAL_MODERATION_WARNING_MESSAGE_LOCATION` is used."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"):
            os.environ["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] = (
                test_manual_moderation_warning_message_location
            )

            RuntimeSettings._setup_strike_performed_manually_warning_location()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"] == (
            test_manual_moderation_warning_message_location.strip()
        )

    def test_default_manual_moderation_warning_message_location(self) -> None:
        """Test a default value used when no `MANUAL_MODERATION_WARNING_MESSAGE_LOCATION`."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"):
            try:
                RuntimeSettings._setup_strike_performed_manually_warning_location()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert isinstance(RuntimeSettings()["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"], str)

        assert bool(RuntimeSettings()["STRIKE_PERFORMED_MANUALLY_WARNING_LOCATION"])


class TestSetupCustomDiscordInviteUrl:
    """Test case for the `_setup_custom_discord_invite_url()` function."""

    @pytest.mark.parametrize(
        "test_custom_discord_invite_url",
        (
            "https://discord.gg/abc123",
            "https://discord.com/invite/abc123",
            "   https://discord.gg/abc123   ",
            "https://cssbham.com",
            "www.cssbham.com/discord",
        ),
    )
    def test_setup_custom_discord_invite_url_successful(
        self, test_custom_discord_invite_url: str
    ) -> None:
        """Test that a given valid `CUSTOM_DISCORD_INVITE_URL` is used when provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CUSTOM_DISCORD_INVITE_URL"):
            os.environ["CUSTOM_DISCORD_INVITE_URL"] = test_custom_discord_invite_url

            RuntimeSettings._setup_custom_discord_invite_url()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["CUSTOM_DISCORD_INVITE_URL"] == (
            f"https://{test_custom_discord_invite_url.strip()}"
            if "://" not in test_custom_discord_invite_url.strip()
            else test_custom_discord_invite_url.strip()
        )

    def test_missing_custom_discord_invite_url(self) -> None:
        """Test that no error is raised when no `CUSTOM_DISCORD_INVITE_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CUSTOM_DISCORD_INVITE_URL"):
            try:
                RuntimeSettings._setup_custom_discord_invite_url()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert not RuntimeSettings()["CUSTOM_DISCORD_INVITE_URL"]

    @pytest.mark.parametrize(
        "test_invalid_discord_invite_url",
        (
            "definitely not a url",
            "https://couldbeaurlbutactually.com really isnt",
            "www.ican'tbelieveit'snotbutter",
        ),
    )
    def test_invalid_custom_discord_invite_url(
        self, test_invalid_discord_invite_url: str
    ) -> None:
        """Test that an error is raised when the `CUSTOM_DISCORD_INVITE_URL` is invalid."""
        INVALID_CUSTOM_DISCORD_INVITE_URL: Final[str] = (
            "CUSTOM_DISCORD_INVITE_URL must be a valid URL."
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CUSTOM_DISCORD_INVITE_URL"):
            os.environ["CUSTOM_DISCORD_INVITE_URL"] = test_invalid_discord_invite_url

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_CUSTOM_DISCORD_INVITE_URL
            ):
                RuntimeSettings._setup_custom_discord_invite_url()


class TestSetupOrganisationID:
    """Test case for the `_setup_organisation_id()` function."""

    @pytest.mark.parametrize(
        "test_organisation_id", ("13471", "43422", "6531", "39091", "41502")
    )
    def test_setup_organisation_id_successful(self, test_organisation_id: str) -> None:
        """Test that the given valid `ORGANISATION_ID` is used when one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("ORGANISATION_ID"):
            os.environ["ORGANISATION_ID"] = test_organisation_id

            RuntimeSettings._setup_organisation_id()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["ORGANISATION_ID"] == test_organisation_id.strip()

    def test_missing_organisation_id(self) -> None:
        """Test that an error is raised when no `ORGANISATION_ID` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with (
            EnvVariableDeleter("ORGANISATION_ID"),
            pytest.raises(
                ImproperlyConfiguredError,
                match="ORGANISATION_ID must be an integer 4 to 5 digits long.",
            ),
        ):
            RuntimeSettings._setup_organisation_id()

    @pytest.mark.parametrize(
        "invalid_organisation_id",
        (
            "invalid_organisation_id",
            "123",
            "123456",
            "12.34",
            "12,34",
            "12.34.56",
            "12,34,56",
            "1234a",
            "a1234",
        ),
    )
    def test_invalid_organisation_id(self, invalid_organisation_id: str) -> None:
        """Test that an error is raised when the provided `ORGANISATION_ID` is invalid."""
        INVALID_ORGANISATION_ID_MESSAGE: Final[str] = (
            "ORGANISATION_ID must be an integer 4 to 5 digits long."
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("ORGANISATION_ID"):
            os.environ["ORGANISATION_ID"] = invalid_organisation_id

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_ORGANISATION_ID_MESSAGE
            ):
                RuntimeSettings._setup_organisation_id()


class TestSetupAutoAddCommitteeToThreads:
    """Test case for the `_setup_auto_add_committee_to_threads()` function."""

    @pytest.mark.parametrize(
        "test_auto_add_committee_to_threads_value",
        (
            "true",
            "false",
            "True",
            "False",
            "   True   ",
            "   False   ",
            "t",
            "f",
            "yes",
            "no",
            "y",
            "n",
            "1",
            "0",
            "   1   ",
            "   0   ",
        ),
    )
    def test_setup_auto_add_committee_to_threads_successful(
        self, test_auto_add_committee_to_threads_value: str
    ) -> None:
        """Test that the given valid `AUTO_ADD_COMMITTEE_TO_THREADS` is used when provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("AUTO_ADD_COMMITTEE_TO_THREADS"):
            os.environ["AUTO_ADD_COMMITTEE_TO_THREADS"] = (
                test_auto_add_committee_to_threads_value
            )

            RuntimeSettings._setup_auto_add_committee_to_threads()

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["AUTO_ADD_COMMITTEE_TO_THREADS"] == (
            test_auto_add_committee_to_threads_value.lower().strip() in config.TRUE_VALUES
        )

    def test_default_auto_add_committee_to_threads_value(self) -> None:
        """Test that the default is used when `AUTO_ADD_COMMITTEE_TO_THREADS` not provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("AUTO_ADD_COMMITTEE_TO_THREADS"):
            try:
                RuntimeSettings._setup_auto_add_committee_to_threads()
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True

        assert RuntimeSettings()["AUTO_ADD_COMMITTEE_TO_THREADS"]

    @pytest.mark.parametrize(
        "invalid_auto_add_commmittee_to_threads",
        (
            "invalid_auto_add_commmittee_to_threads",
            "definitely not a valid value",
            "won d e r i f t h i s a valid value",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=8),
            ),
        ),
        ids=[f"case_{i}" for i in range(4)],
    )
    def test_invalid_auto_add_commmittee_to_threads(
        self, invalid_auto_add_commmittee_to_threads: str
    ) -> None:
        """Test that an error is raised when is `AUTO_ADD_COMMITTEE_TO_THREADS` invalid."""
        INVALID_AUTO_ADD_COMMITTEE_TO_THREADS_MESSAGE: Final[str] = (
            "AUTO_ADD_COMMITTEE_TO_THREADS must be a boolean value"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("AUTO_ADD_COMMITTEE_TO_THREADS"):
            os.environ["AUTO_ADD_COMMITTEE_TO_THREADS"] = (
                invalid_auto_add_commmittee_to_threads
            )

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_AUTO_ADD_COMMITTEE_TO_THREADS_MESSAGE
            ):
                RuntimeSettings._setup_auto_add_committee_to_threads()
