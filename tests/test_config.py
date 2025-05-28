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
from tests._testing_utils import EnvVariableDeleter, FileTemporaryDeleter

from .test_utils._testing_utils import (
    RandomDiscordBotTokenGenerator,
    RandomDiscordGuildIDGenerator,
    RandomDiscordLogChannelWebhookURLGenerator,
    RandomOrganisationIDGenerator,
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

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        SETUP_METHOD_NAMES: Final[Iterable[str]] = {
            setup_method_name
            for setup_method_name in dir(RuntimeSettings)
            if (
                setup_method_name.startswith("_setup_")
                and setup_method_name not in ignore_methods
            )
        }

        if not SETUP_METHOD_NAMES:
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

    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getattr_success(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:  # noqa: N803
        """Test that retrieving a settings variable by attr-lookup returns the set value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert getattr(RuntimeSettings(), TEST_ITEM_NAME) == TEST_ITEM_VALUE

    @pytest.mark.parametrize("MISSING_ITEM_NAME", ("ITEM",))
    def test_getattr_missing_item(self, MISSING_ITEM_NAME: str) -> None:  # noqa: N803
        """
        Test that requesting a missing settings variable by attribute-lookup raises an error.

        A missing settings variable is one that has a valid name,
        but does not exist within the `_settings` dict (i.e. has not been set).
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        with pytest.raises(
            AttributeError, match=f"'{MISSING_ITEM_NAME}' is not a valid settings key."
        ):
            assert getattr(RuntimeSettings(), MISSING_ITEM_NAME)

    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1", "ITEM__1", "!ITEM_1"))
    def test_getattr_invalid_name(self, INVALID_ITEM_NAME: str) -> None:  # noqa: N803
        """Test that requesting an invalid settings variable by attr-lookup raises an error."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        with pytest.raises(AttributeError, match=f"no attribute {INVALID_ITEM_NAME!r}"):
            assert getattr(RuntimeSettings(), INVALID_ITEM_NAME)

    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getattr_sets_up_env_variables(
        self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str
    ) -> None:
        """
        Test that requesting a settings variable sets them all up if they have not been.

        This test requests the settings variable by attribute-lookup.
        """
        is_env_variables_setup: bool = False

        def set_is_env_variables_setup(_instance: Settings | None = None) -> None:
            nonlocal is_env_variables_setup
            is_env_variables_setup = True

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE  # noqa: SLF001
        RuntimeSettings._setup_env_variables = set_is_env_variables_setup  # type: ignore[method-assign] # noqa: SLF001

        getattr(RuntimeSettings(), TEST_ITEM_NAME)

        assert is_env_variables_setup is True

    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getitem_success(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:  # noqa: N803
        """Test that retrieving a settings variable by key-lookup returns the set value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()[TEST_ITEM_NAME] == TEST_ITEM_VALUE

    @pytest.mark.parametrize("MISSING_ITEM_NAME", ("ITEM",))
    def test_getitem_missing_item(self, MISSING_ITEM_NAME: str) -> None:  # noqa: N803
        """
        Test that requesting a missing settings variable by key-lookup raises an error.

        A missing settings variable is one that has a valid name,
        but does not exist within the `_settings` dict (i.e. has not been set).
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        with pytest.raises(
            KeyError, match=f"'{MISSING_ITEM_NAME}' is not a valid settings key."
        ):
            assert RuntimeSettings()[MISSING_ITEM_NAME]

    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1", "ITEM__1", "!ITEM_1"))
    def test_getitem_invalid_name(self, INVALID_ITEM_NAME: str) -> None:  # noqa: N803
        """Test that requesting an invalid settings variable by key-lookup raises an error."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        with pytest.raises(KeyError, match=str(KeyError(INVALID_ITEM_NAME))):
            assert RuntimeSettings()[INVALID_ITEM_NAME]

    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getitem_sets_up_env_variables(
        self,
        TEST_ITEM_NAME: str,
        TEST_ITEM_VALUE: str,  # noqa: N803
    ) -> None:
        """
        Test that requesting a settings variable sets them all up if they have not been.

        This test requests the settings variable by key-lookup.
        """
        is_env_variables_setup: bool = False

        def set_is_env_variables_setup(_instance: Settings | None = None) -> None:
            nonlocal is_env_variables_setup
            is_env_variables_setup = True

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE  # noqa: SLF001
        RuntimeSettings._setup_env_variables = set_is_env_variables_setup  # type: ignore[method-assign] # noqa: SLF001

        RuntimeSettings().__getitem__(TEST_ITEM_NAME)

        assert is_env_variables_setup is True

    def test_is_env_variables_setup_made_true(self) -> None:
        """Test calling `_setup_env_variables()` sets `_is_env_variables_setup` to True."""
        RuntimeSettings: Final[type[Settings]] = self.replace_setup_methods(
            ignore_methods=("_setup_env_variables",),
        )

        assert RuntimeSettings._is_env_variables_setup is False  # noqa: SLF001

        RuntimeSettings._setup_env_variables()  # noqa: SLF001

        assert RuntimeSettings._is_env_variables_setup is True  # noqa: SLF001

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

        RuntimeSettings._setup_env_variables()  # noqa: SLF001

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

    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_cannot_setup_more_than_once(
        self,
        caplog: "LogCaptureFixture",
        TEST_ITEM_NAME: str,
        TEST_ITEM_VALUE: str,  # noqa: N803
    ) -> None:
        """Test that the Env Variables cannot be set more than once."""
        RuntimeSettings: Final[type[Settings]] = self.replace_setup_methods(
            ignore_methods=("_setup_env_variables",),
        )

        RuntimeSettings._setup_env_variables()  # noqa: SLF001
        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE  # noqa: SLF001

        PREVIOUS_SETTINGS: Final[dict[str, object]] = RuntimeSettings._settings.copy()  # noqa: SLF001

        assert not caplog.text

        RuntimeSettings._setup_env_variables()  # noqa: SLF001

        assert RuntimeSettings._settings == PREVIOUS_SETTINGS  # noqa: SLF001
        assert "already" in caplog.text
        assert "set up" in caplog.text

    def test_module_level_settings_object(self) -> None:
        """Test that the auto-instantiated module-level settings object is correct."""
        assert isinstance(config.settings, Settings)

    def test_settings_class_factory(self) -> None:
        """Test that the settings class factory produces valid & separate settings classes."""
        assert issubclass(config._settings_class_factory(), Settings)  # noqa: SLF001

        assert config._settings_class_factory()._is_env_variables_setup is False  # noqa: SLF001
        assert not config._settings_class_factory()._settings  # noqa: SLF001

        assert config._settings_class_factory() != config._settings_class_factory()  # noqa: SLF001


class TestSetupLogging:
    """Test case to unit-test the `_setup_logging()` function."""

    @pytest.mark.parametrize("TEST_LOG_LEVEL", config.LOG_LEVEL_CHOICES)
    def test_setup_logging_successful(self, TEST_LOG_LEVEL: str) -> None:  # noqa: N803
        """Test that the given `CONSOLE_LOG_LEVEL` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = TEST_LOG_LEVEL

            RuntimeSettings._setup_logging()  # noqa: SLF001

        assert "TeX-Bot" in set(logging.root.manager.loggerDict)
        assert logging.getLogger("TeX-Bot").getEffectiveLevel() == getattr(
            logging, TEST_LOG_LEVEL
        )

    def test_default_console_log_level(self) -> None:
        """Test that a default value is used when no `CONSOLE_LOG_LEVEL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            RuntimeSettings._setup_logging()  # noqa: SLF001

        assert "TeX-Bot" in set(logging.root.manager.loggerDict)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_LOG_LEVEL",
        (
            "INVALID_LOG_LEVEL",
            "",
            "  ",
            "".join(
                random.choices(
                    string.ascii_letters + string.digits + string.punctuation,
                    k=18,
                ),
            ),
        ),
    )
    def test_invalid_console_log_level(self, INVALID_LOG_LEVEL: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `CONSOLE_LOG_LEVEL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = INVALID_LOG_LEVEL

            with pytest.raises(ImproperlyConfiguredError, match="LOG_LEVEL must be one of"):
                RuntimeSettings._setup_logging()  # noqa: SLF001

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("LOWERCASE_LOG_LEVEL", ("info",))
    def test_valid_lowercase_console_log_level(self, LOWERCASE_LOG_LEVEL: str) -> None:  # noqa: N803
        """Test that the provided `CONSOLE_LOG_LEVEL` is fixed & used if it is in lowercase."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = LOWERCASE_LOG_LEVEL

            RuntimeSettings._setup_logging()  # noqa: SLF001


class TestSetupDiscordBotToken:
    """Test case to unit-test the `_setup_discord_bot_token()` function."""

    @pytest.mark.parametrize(
        "TEST_DISCORD_BOT_TOKEN",
        itertools.chain(
            RandomDiscordBotTokenGenerator.multiple_values(),
            (f"    {RandomDiscordBotTokenGenerator.single_value()}   ",),
        ),
    )
    def test_setup_discord_bot_token_successful(self, TEST_DISCORD_BOT_TOKEN: str) -> None:  # noqa: N803
        """Test that the given `DISCORD_BOT_TOKEN` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_BOT_TOKEN"):
            os.environ["DISCORD_BOT_TOKEN"] = TEST_DISCORD_BOT_TOKEN

            RuntimeSettings._setup_discord_bot_token()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["DISCORD_BOT_TOKEN"] == TEST_DISCORD_BOT_TOKEN.strip()

    def test_missing_discord_bot_token(self) -> None:
        """Test that an error is raised when no `DISCORD_BOT_TOKEN` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_BOT_TOKEN"):  # noqa: SIM117
            with pytest.raises(
                ImproperlyConfiguredError, match=r"DISCORD_BOT_TOKEN.*valid.*Discord bot token"
            ):
                RuntimeSettings._setup_discord_bot_token()  # noqa: SLF001

    @pytest.mark.parametrize(
        "INVALID_DISCORD_BOT_TOKEN",
        (
            "INVALID_DISCORD_BOT_TOKEN",
            "",
            "  ",
            "".join(
                random.choices(  # noqa: S311
                    string.ascii_letters + string.digits + string.punctuation,
                    k=18,
                ),
            ),
            re.sub(
                r"\A[A-Za-z0-9]{24,26}\.",
                f"{''.join(random.choices(string.ascii_letters + string.digits, k=2))}.",  # noqa: S311
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\A[A-Za-z0-9]{24,26}\.",
                f"{''.join(random.choices(string.ascii_letters + string.digits, k=50))}.",  # noqa: S311
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\A[A-Za-z0-9]{24,26}\.",
                (
                    f"{''.join(random.choices(string.ascii_letters + string.digits, k=12))}>{
                        ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                    }."  # noqa: S311
                ),
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\.[A-Za-z0-9]{6}\.",
                f".{''.join(random.choices(string.ascii_letters + string.digits, k=2))}.",  # noqa: S311
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\.[A-Za-z0-9]{6}\.",
                (f".{''.join(random.choices(string.ascii_letters + string.digits, k=50))}."),  # noqa: S311
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"\.[A-Za-z0-9]{6}\.",
                (
                    f".{''.join(random.choices(string.ascii_letters + string.digits, k=3))}>{
                        ''.join(random.choices(string.ascii_letters + string.digits, k=2))
                    }."  # noqa: S311
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
                    }"  # noqa: S311
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
                    }"  # noqa: S311
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
                    }"  # noqa: S311
                ),
                string=RandomDiscordBotTokenGenerator.single_value(),
                count=1,
            ),
        ),
    )
    def test_invalid_discord_bot_token(self, INVALID_DISCORD_BOT_TOKEN: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `DISCORD_BOT_TOKEN` is provided."""
        INVALID_DISCORD_BOT_TOKEN_MESSAGE: Final[str] = (
            "DISCORD_BOT_TOKEN must be a valid Discord bot token"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_BOT_TOKEN"):
            os.environ["DISCORD_BOT_TOKEN"] = INVALID_DISCORD_BOT_TOKEN

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_DISCORD_BOT_TOKEN_MESSAGE
            ):
                RuntimeSettings._setup_discord_bot_token()  # noqa: SLF001


class TestSetupDiscordLogChannelWebhookURL:
    """Test case to unit-test the `_setup_discord_log_channel_webhook()` function."""

    @pytest.mark.parametrize(
        "TEST_DISCORD_LOG_CHANNEL_WEBHOOK_URL",
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
    )
    def test_setup_discord_log_channel_webhook_successful(
        self,
        TEST_DISCORD_LOG_CHANNEL_WEBHOOK_URL: str,  # noqa: N803
    ) -> None:
        """
        Test that the given `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is used when provided.

        In this test, the provided `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is valid
        and so must be saved successfully.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_LOG_CHANNEL_WEBHOOK_URL"):
            os.environ["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = (
                TEST_DISCORD_LOG_CHANNEL_WEBHOOK_URL
            )

            RuntimeSettings._setup_discord_log_channel_webhook()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] == (
            TEST_DISCORD_LOG_CHANNEL_WEBHOOK_URL.strip()
        )

    def test_missing_discord_log_channel_webhook_url(self) -> None:
        """Test that no error occurs when no `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_LOG_CHANNEL_WEBHOOK_URL"):
            try:
                RuntimeSettings._setup_discord_log_channel_webhook()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert not RuntimeSettings()["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]

    @pytest.mark.parametrize(
        "INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL",
        (
            "INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL",
            "",
            "  ",
            "".join(
                random.choices(  # noqa: S311
                    string.ascii_letters + string.digits + string.punctuation,
                    k=18,
                ),
            ),
            re.sub(
                r"/\d{17,20}/",
                f"/{''.join(random.choices(string.digits, k=2))}/",  # noqa: S311
                string=RandomDiscordLogChannelWebhookURLGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"/\d{17,20}/",
                f"/{''.join(random.choices(string.digits, k=50))}/",  # noqa: S311
                string=RandomDiscordLogChannelWebhookURLGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"/\d{17,20}/",
                (
                    f"/{''.join(random.choices(string.ascii_letters + string.digits, k=9))}>{
                        ''.join(random.choices(string.ascii_letters + string.digits, k=9))
                    }/"  # noqa: S311
                ),
                string=RandomDiscordLogChannelWebhookURLGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"/[a-zA-Z\d]{60,90}",
                f"/{''.join(random.choices(string.ascii_letters + string.digits, k=2))}",  # noqa: S311
                string=RandomDiscordLogChannelWebhookURLGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"/[a-zA-Z\d]{60,90}",
                (f"/{''.join(random.choices(string.ascii_letters + string.digits, k=150))}"),  # noqa: S311
                string=RandomDiscordLogChannelWebhookURLGenerator.single_value(),
                count=1,
            ),
            re.sub(
                r"/[a-zA-Z\d]{60,90}",
                (
                    f"/{''.join(random.choices(string.ascii_letters + string.digits, k=37))}>{
                        ''.join(random.choices(string.ascii_letters + string.digits, k=37))
                    }"  # noqa: S311
                ),
                string=RandomDiscordLogChannelWebhookURLGenerator.single_value(),
                count=1,
            ),
        ),
        ids=[f"case_{i}" for i in range(10)]
    )
    def test_invalid_discord_log_channel_webhook_url(
        self,
        INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL: str,  # noqa: N803
    ) -> None:
        """Test that an error occurs when `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is invalid."""
        INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE: Final[str] = (
            "DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL "
            "that points to a discord channel where logs should be displayed."
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_LOG_CHANNEL_WEBHOOK_URL"):
            os.environ["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = (
                INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL
            )

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE,
            ):
                RuntimeSettings._setup_discord_log_channel_webhook()  # noqa: SLF001


class TestSetupDiscordGuildID:
    """Test case to unit-test the `_setup_discord_guild_id()` function."""

    @pytest.mark.parametrize(
        "TEST_DISCORD_GUILD_ID",
        itertools.chain(
            RandomDiscordGuildIDGenerator.multiple_values(),
            (f"    {RandomDiscordGuildIDGenerator.single_value()}   ",),
        ),
    )
    def test_setup_discord_guild_id_successful(self, TEST_DISCORD_GUILD_ID: str) -> None:  # noqa: N803
        """Test that the given `DISCORD_GUILD_ID` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_GUILD_ID"):
            os.environ["DISCORD_GUILD_ID"] = TEST_DISCORD_GUILD_ID

            RuntimeSettings._setup_discord_guild_id()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["DISCORD_GUILD_ID"] == int(TEST_DISCORD_GUILD_ID.strip())

    def test_missing_discord_guild_id(self) -> None:
        """Test that an error is raised when no `DISCORD_GUILD_ID` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_GUILD_ID"):  # noqa: SIM117
            with pytest.raises(
                ImproperlyConfiguredError, match=r"DISCORD_GUILD_ID.*valid.*Discord guild ID"
            ):
                RuntimeSettings._setup_discord_guild_id()  # noqa: SLF001

    @pytest.mark.parametrize(
        "INVALID_DISCORD_GUILD_ID",
        (
            "INVALID_DISCORD_GUILD_ID",
            "",
            "  ",
            "".join(
                random.choices(  # noqa: S311
                    string.ascii_letters + string.digits + string.punctuation,
                    k=18,
                ),
            ),
            "".join(random.choices(string.digits, k=2)),  # noqa: S311
            "".join(random.choices(string.digits, k=50)),  # noqa: S311
        ),
    )
    def test_invalid_discord_guild_id(self, INVALID_DISCORD_GUILD_ID: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `DISCORD_GUILD_ID` is provided."""
        INVALID_DISCORD_GUILD_ID_MESSAGE: Final[str] = (
            "DISCORD_GUILD_ID must be a valid Discord guild ID"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_GUILD_ID"):
            os.environ["DISCORD_GUILD_ID"] = INVALID_DISCORD_GUILD_ID

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_DISCORD_GUILD_ID_MESSAGE
            ):
                RuntimeSettings._setup_discord_guild_id()  # noqa: SLF001


class TestSetupGroupFullName:
    """Test case to unit-test the `_setup_group_full_name()` function."""

    @pytest.mark.parametrize(
        "TEST_GROUP_FULL_NAME",
        (
            "Computer Science Society",
            "Arts & Crafts Soc",
            "3Bugs Fringe Theatre Society",
            "Bahá’í",  # noqa: RUF001
            "Burn FM.com",
            "Dental Society (BUDSS)",
            "Devil's Advocate Society",
            "KASE: Knowledge And Skills Exchange",
            "Law for Non-Law",
            "   Computer Science Society    ",
            "Computer Science Society?",
            "Computer Science Society!",
            "(Computer Science Society)",
        ),
    )
    def test_setup_group_full_name_successful(self, TEST_GROUP_FULL_NAME: str) -> None:  # noqa: N803
        """Test that the given `GROUP_NAME` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("GROUP_NAME"):
            os.environ["GROUP_NAME"] = TEST_GROUP_FULL_NAME

            RuntimeSettings._setup_group_full_name()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["_GROUP_FULL_NAME"] == TEST_GROUP_FULL_NAME.strip().translate(
            {
                ord(unicode_char): ascii_char
                for unicode_char, ascii_char in zip("‘’´“”–-", "''`\"\"--", strict=True)  # noqa: RUF001
            },
        )

    def test_missing_group_full_name(self) -> None:
        """Test that no error occurs when no `GROUP_NAME` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("GROUP_NAME"):
            try:
                RuntimeSettings._setup_group_full_name()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert not RuntimeSettings()["_GROUP_FULL_NAME"]

    @pytest.mark.parametrize(
        "INVALID_GROUP_FULL_NAME",
        (
            "Computer  Science  Society",
            "Computer Science..Society",
            "Computer Science--Society",
            "Computer Science&&Society",
            "Computer Science%%Society",
            "Computer Science$Society",
            "Computer Science£Society",
            "Computer Science*Society",
            "Computer Science Society&",
            "Computer Science Society-",
            "Computer Science Society,",
            "!Computer Science Society",
            "?Computer Science Society",
            "&Computer Science Society",
            ":Computer Science Society",
            ",Computer Science Society",
            ".Computer Science Society",
            "%Computer Science Society",
            "-Computer Science Society",
            "",
            "  ",
            "".join(random.choices(string.digits, k=30)),  # noqa: S311
        ),
    )
    def test_invalid_group_full_name(self, INVALID_GROUP_FULL_NAME: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `GROUP_NAME` is provided."""
        INVALID_GROUP_NAME_MESSAGE: Final[str] = (
            "GROUP_NAME must not contain any invalid characters"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("GROUP_NAME"):
            os.environ["GROUP_NAME"] = INVALID_GROUP_FULL_NAME

            with pytest.raises(ImproperlyConfiguredError, match=INVALID_GROUP_NAME_MESSAGE):
                RuntimeSettings._setup_group_full_name()  # noqa: SLF001


class TestSetupGroupShortName:
    """Test case to unit-test the `_setup_group_short_name()` function."""

    @pytest.mark.parametrize(
        "TEST_GROUP_SHORT_NAME",
        (
            "CSS",
            "ArtSoc",
            "3Bugs",
            "Bahá’í",  # noqa: RUF001
            "BurnFM.com",
            "L4N-L",
            "   CSS    ",
            "CSS?",
            "CSS!",
            "(CSS)",
        ),
    )
    def test_setup_group_short_name_successful(self, TEST_GROUP_SHORT_NAME: str) -> None:  # noqa: N803
        """Test that the given `GROUP_SHORT_NAME` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("GROUP_SHORT_NAME"):
            os.environ["GROUP_SHORT_NAME"] = TEST_GROUP_SHORT_NAME

            RuntimeSettings._setup_group_short_name()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["_GROUP_SHORT_NAME"] == (
            TEST_GROUP_SHORT_NAME.strip().translate(
                {
                    ord(unicode_char): ascii_char
                    for unicode_char, ascii_char in zip("‘’´“”–-", "''`\"\"--", strict=True)  # noqa: RUF001
                },
            )
        )

    def test_missing_group_short_name_without_group_full_name(self) -> None:
        """Test that no error occurs when no `GROUP_SHORT_NAME` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("GROUP_SHORT_NAME"), EnvVariableDeleter("GROUP_NAME"):
            RuntimeSettings._setup_group_full_name()  # noqa: SLF001
            assert RuntimeSettings._settings["_GROUP_FULL_NAME"] is None  # noqa: SLF001

            try:
                RuntimeSettings._setup_group_short_name()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert not RuntimeSettings()["_GROUP_SHORT_NAME"]

    # noinspection PyPep8Naming,SpellCheckingInspection
    @pytest.mark.parametrize(
        "TEST_GROUP_FULL_NAME",
        (
            "Computer Science Society",
            "Arts & Crafts Soc",
            "3Bugs Fringe Theatre Society",
            "Bahá’í",  # noqa: RUF001
            "Burn FM.com",
            "Dental Society (BUDSS)",
            "Devil's Advocate Society",
            "KASE: Knowledge And Skills Exchange",
            "Law for Non-Law",
            "   Computer Science Society    ",
            "Computer Science Society?",
            "Computer Science Society!",
            "(Computer Science Society)",
        ),
    )
    def test_resolved_value_group_short_name_with_group_full_name(
        self,
        TEST_GROUP_FULL_NAME: str,  # noqa: N803
    ) -> None:
        """
        Test that a resolved value is used when no `GROUP_SHORT_NAME` is provided.

        This test runs with the given value for `GROUP_FULL_NAME`,
        so a resolved value from that should be used for the `GROUP_SHORT_NAME`.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("GROUP_SHORT_NAME"), EnvVariableDeleter("GROUP_NAME"):
            os.environ["GROUP_NAME"] = TEST_GROUP_FULL_NAME
            RuntimeSettings._setup_group_full_name()  # noqa: SLF001

            try:
                RuntimeSettings._setup_group_short_name()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert (
            RuntimeSettings()["_GROUP_SHORT_NAME"]
            == (
                "CSS"
                if (
                    "computer science society" in TEST_GROUP_FULL_NAME.lower()
                    or "css" in TEST_GROUP_FULL_NAME.lower()
                )
                else TEST_GROUP_FULL_NAME
            )
            .replace(
                "the",
                "",
            )
            .replace(
                "THE",
                "",
            )
            .replace(
                "The",
                "",
            )
            .replace(
                " ",
                "",
            )
            .replace(
                "\t",
                "",
            )
            .replace(
                "\n",
                "",
            )
            .translate(
                {
                    ord(unicode_char): ascii_char
                    for unicode_char, ascii_char in zip("‘’´“”–-", "''`\"\"--", strict=True)  # noqa: RUF001
                },
            )
            .strip()
        )

    @pytest.mark.parametrize(
        "INVALID_GROUP_SHORT_NAME",
        (
            "C S S",
            "CS..S",
            "CS--S",
            "CS&&S",
            "CS%%S",
            "CS$S",
            "CS£S",
            "CSS&",
            "CS*S",
            "CSS-",
            "CSS,",
            "!CSS",
            "?CSS",
            "&CSS",
            ":CSS",
            ",CSS",
            ".CSS",
            "%CSS",
            "-CSS",
            "",
            "  ",
            "".join(random.choices(string.digits, k=30)),
        ),
    )
    def test_invalid_group_short_name(self, INVALID_GROUP_SHORT_NAME: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `GROUP_SHORT_NAME` is provided."""
        INVALID_GROUP_SHORT_NAME_MESSAGE: Final[str] = (
            "GROUP_SHORT_NAME must not contain any invalid characters"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("GROUP_SHORT_NAME"):
            os.environ["GROUP_SHORT_NAME"] = INVALID_GROUP_SHORT_NAME

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_GROUP_SHORT_NAME_MESSAGE
            ):
                RuntimeSettings._setup_group_short_name()  # noqa: SLF001


class TestSetupPurchaseMembershipURL:
    """Test case to unit-test the `_setup_purchase_membership_url()` function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_PURCHASE_MEMBERSHIP_URL",
        ("https://google.com", "www.google.com/", "    https://google.com   "),
    )
    def test_setup_purchase_membership_url_successful(
        self, TEST_PURCHASE_MEMBERSHIP_URL: str
    ) -> None:
        """Test that the given valid `PURCHASE_MEMBERSHIP_URL` is used when one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("PURCHASE_MEMBERSHIP_URL"):
            os.environ["PURCHASE_MEMBERSHIP_URL"] = TEST_PURCHASE_MEMBERSHIP_URL

            RuntimeSettings._setup_purchase_membership_url()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["PURCHASE_MEMBERSHIP_URL"] == (
            f"https://{TEST_PURCHASE_MEMBERSHIP_URL.strip()}"
            if "://" not in TEST_PURCHASE_MEMBERSHIP_URL
            else TEST_PURCHASE_MEMBERSHIP_URL.strip()
        )

    def test_missing_purchase_membership_url(self) -> None:
        """Test that no error occurs when no `PURCHASE_MEMBERSHIP_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("PURCHASE_MEMBERSHIP_URL"):
            try:
                RuntimeSettings._setup_purchase_membership_url()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert not RuntimeSettings()["PURCHASE_MEMBERSHIP_URL"]

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_PURCHASE_MEMBERSHIP_URL",
        ("INVALID_PURCHASE_MEMBERSHIP_URL", "www.google..com/", "", "  "),
    )
    def test_invalid_purchase_membership_url(
        self, INVALID_PURCHASE_MEMBERSHIP_URL: str
    ) -> None:
        """Test that an error occurs when the provided `PURCHASE_MEMBERSHIP_URL` is invalid."""
        INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE: Final[str] = (
            "PURCHASE_MEMBERSHIP_URL must be a valid URL"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("PURCHASE_MEMBERSHIP_URL"):
            os.environ["PURCHASE_MEMBERSHIP_URL"] = INVALID_PURCHASE_MEMBERSHIP_URL

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_PURCHASE_MEMBERSHIP_URL_MESSAGE
            ):
                RuntimeSettings._setup_purchase_membership_url()  # noqa: SLF001


class TestSetupMembershipPerksURL:
    """Test case to unit-test the `_setup_membership_perks_url()` function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_MEMBERSHIP_PERKS_URL",
        ("https://google.com", "www.google.com/", "    https://google.com   "),
    )
    def test_setup_membership_perks_url_successful(
        self, TEST_MEMBERSHIP_PERKS_URL: str
    ) -> None:
        """Test that the given valid `MEMBERSHIP_PERKS_URL` is used when one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MEMBERSHIP_PERKS_URL"):
            os.environ["MEMBERSHIP_PERKS_URL"] = TEST_MEMBERSHIP_PERKS_URL

            RuntimeSettings._setup_membership_perks_url()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["MEMBERSHIP_PERKS_URL"] == (
            f"https://{TEST_MEMBERSHIP_PERKS_URL.strip()}"
            if "://" not in TEST_MEMBERSHIP_PERKS_URL.strip()
            else TEST_MEMBERSHIP_PERKS_URL.strip()
        )

    def test_missing_membership_perks_url(self) -> None:
        """Test that no error occurs when no `MEMBERSHIP_PERKS_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MEMBERSHIP_PERKS_URL"):
            try:
                RuntimeSettings._setup_membership_perks_url()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert not RuntimeSettings()["MEMBERSHIP_PERKS_URL"]

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_MEMBERSHIP_PERKS_URL",
        ("INVALID_MEMBERSHIP_PERKS_URL", "www.google..com/", "", "  "),
    )
    def test_invalid_membership_perks_url(self, INVALID_MEMBERSHIP_PERKS_URL: str) -> None:  # noqa: N803
        """Test that an error occurs when the provided `MEMBERSHIP_PERKS_URL` is invalid."""
        INVALID_MEMBERSHIP_PERKS_URL_MESSAGE: Final[str] = (
            "MEMBERSHIP_PERKS_URL must be a valid URL"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MEMBERSHIP_PERKS_URL"):
            os.environ["MEMBERSHIP_PERKS_URL"] = INVALID_MEMBERSHIP_PERKS_URL

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_MEMBERSHIP_PERKS_URL_MESSAGE
            ):
                RuntimeSettings._setup_membership_perks_url()  # noqa: SLF001


class TestSetupPingCommandEasterEggProbability:
    """Test case to unit-test the `_setup_ping_command_easter_egg_probability()` function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_PING_COMMAND_EASTER_EGG_PROBABILITY",
        ("1", "0", "0.5", "    0.5   "),
    )
    def test_setup_ping_command_easter_egg_probability_successful(
        self, TEST_PING_COMMAND_EASTER_EGG_PROBABILITY: str
    ) -> None:
        """
        Test that the given `PING_COMMAND_EASTER_EGG_PROBABILITY` is used when provided.

        In this test, the provided `PING_COMMAND_EASTER_EGG_PROBABILITY` is valid
        and so must be saved successfully.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("PING_COMMAND_EASTER_EGG_PROBABILITY"):
            os.environ["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
                TEST_PING_COMMAND_EASTER_EGG_PROBABILITY
            )

            RuntimeSettings._setup_ping_command_easter_egg_probability()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["PING_COMMAND_EASTER_EGG_PROBABILITY"] == 100 * float(
            TEST_PING_COMMAND_EASTER_EGG_PROBABILITY.strip(),
        )

    def test_default_ping_command_easter_egg_probability(self) -> None:
        """Test that a default value is used if no `PING_COMMAND_EASTER_EGG_PROBABILITY`."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("PING_COMMAND_EASTER_EGG_PROBABILITY"):
            try:
                RuntimeSettings._setup_ping_command_easter_egg_probability()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert isinstance(RuntimeSettings()["PING_COMMAND_EASTER_EGG_PROBABILITY"], float)
        assert 0 <= RuntimeSettings()["PING_COMMAND_EASTER_EGG_PROBABILITY"] <= 100

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY",
        ("INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY", "", "  ", "-5", "1.1", "5", "-0.01"),
    )
    def test_invalid_ping_command_easter_egg_probability(
        self, INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY: str
    ) -> None:
        """Test that errors when provided `PING_COMMAND_EASTER_EGG_PROBABILITY` is invalid."""
        INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE: Final[str] = (
            r"PING_COMMAND_EASTER_EGG_PROBABILITY must be a float.*between.*1.*0"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("PING_COMMAND_EASTER_EGG_PROBABILITY"):
            os.environ["PING_COMMAND_EASTER_EGG_PROBABILITY"] = (
                INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY
            )

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_PING_COMMAND_EASTER_EGG_PROBABILITY_MESSAGE,
            ):
                RuntimeSettings._setup_ping_command_easter_egg_probability()  # noqa: SLF001


class TestSetupMessagesFile:
    """Test case to unit-test all functions that use/relate to the messages JSON file."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "RAW_INVALID_MESSAGES_FILE_PATH",
        ("messages.json.invalid", "", "  "),
    )
    def test_get_messages_dict_with_invalid_messages_file_path(
        self, RAW_INVALID_MESSAGES_FILE_PATH: str
    ) -> None:
        """Test that an error occurs when the provided `messages_file_path` is invalid."""
        INVALID_MESSAGES_FILE_PATH: Path = Path(RAW_INVALID_MESSAGES_FILE_PATH.strip())

        with FileTemporaryDeleter(INVALID_MESSAGES_FILE_PATH):
            INVALID_MESSAGES_FILE_PATH_MESSAGE: Final[str] = (
                "MESSAGES_FILE_PATH must be a path to a file that exists"
            )
            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_MESSAGES_FILE_PATH_MESSAGE
            ):
                Settings._get_messages_dict(RAW_INVALID_MESSAGES_FILE_PATH)  # noqa: SLF001

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_MESSAGES_DICT", ({"welcome_messages": ["Welcome!"]},))
    def test_get_messages_dict_with_no_messages_file_path(
        self, TEST_MESSAGES_DICT: "Mapping[str, object]"
    ) -> None:
        """Test that the default value is used when no `messages_file_path` is provided."""
        DEFAULT_MESSAGES_FILE_PATH: Path = config.PROJECT_ROOT / "messages.json"

        with FileTemporaryDeleter(DEFAULT_MESSAGES_FILE_PATH):
            default_messages_file: TextIO
            with DEFAULT_MESSAGES_FILE_PATH.open("w") as default_messages_file:
                json.dump(TEST_MESSAGES_DICT, fp=default_messages_file)

            assert (
                Settings._get_messages_dict(raw_messages_file_path=None) == TEST_MESSAGES_DICT  # noqa: SLF001
            )

            DEFAULT_MESSAGES_FILE_PATH.unlink()

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_MESSAGES_DICT", ({"welcome_messages": ["Welcome!"]},))
    def test_get_messages_dict_successful(
        self, TEST_MESSAGES_DICT: "Mapping[str, object]"
    ) -> None:
        """Test that the given path is used when a `messages_file_path` is provided."""
        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(TEST_MESSAGES_DICT, fp=temporary_messages_file)

            temporary_messages_file.close()

            assert (
                Settings._get_messages_dict(  # noqa: SLF001
                    raw_messages_file_path=temporary_messages_file.name,
                )
                == TEST_MESSAGES_DICT
            )

            assert (
                Settings._get_messages_dict(  # noqa: SLF001
                    raw_messages_file_path=f"  {temporary_messages_file.name}   ",
                )
                == TEST_MESSAGES_DICT
            )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_MESSAGES_JSON",
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
    def test_get_messages_dict_with_invalid_json(self, INVALID_MESSAGES_JSON: str) -> None:  # noqa: N803
        """Test that an error is raised when the messages-file contains invalid JSON."""
        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            temporary_messages_file.write(INVALID_MESSAGES_JSON)

            temporary_messages_file.close()

            INVALID_MESSAGES_JSON_MESSAGE: Final[str] = (
                "Messages JSON file must contain a JSON string"
            )
            with pytest.raises(ImproperlyConfiguredError, match=INVALID_MESSAGES_JSON_MESSAGE):
                Settings._get_messages_dict(  # noqa: SLF001
                    raw_messages_file_path=temporary_messages_file.name,
                )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_MESSAGES_DICT", ({"welcome_messages": ["Welcome!"]},))
    def test_setup_welcome_messages_successful_with_messages_file_path(
        self, TEST_MESSAGES_DICT: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that correct welcome messages are loaded when `MESSAGES_FILE_PATH` is valid."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(TEST_MESSAGES_DICT, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                RuntimeSettings._setup_welcome_messages()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["WELCOME_MESSAGES"] == set(
            TEST_MESSAGES_DICT["welcome_messages"],
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_MESSAGES_DICT", ({"welcome_messages": ["Welcome!"]},))
    def test_setup_welcome_messages_successful_with_no_messages_file_path(
        self, TEST_MESSAGES_DICT: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that correct welcome messages are loaded when no `MESSAGES_FILE_PATH` given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        DEFAULT_MESSAGES_FILE_PATH: Path = config.PROJECT_ROOT / "messages.json"

        with FileTemporaryDeleter(DEFAULT_MESSAGES_FILE_PATH):
            default_messages_file: TextIO
            with DEFAULT_MESSAGES_FILE_PATH.open("w") as default_messages_file:
                json.dump(TEST_MESSAGES_DICT, fp=default_messages_file)

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                RuntimeSettings._setup_welcome_messages()  # noqa: SLF001

            DEFAULT_MESSAGES_FILE_PATH.unlink()

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["WELCOME_MESSAGES"] == set(
            TEST_MESSAGES_DICT["welcome_messages"],
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("NO_WELCOME_MESSAGES_DICT", ({"other_messages": ["Welcome!"]},))
    def test_welcome_messages_key_not_in_messages_json(
        self, NO_WELCOME_MESSAGES_DICT: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that error is raised when messages-file not contain `welcome_messages` key."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(NO_WELCOME_MESSAGES_DICT, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                exc_info: ExceptionInfo[MessagesJSONFileMissingKeyError]
                with pytest.raises(MessagesJSONFileMissingKeyError) as exc_info:
                    RuntimeSettings._setup_welcome_messages()  # noqa: SLF001

        assert exc_info.value.missing_key == "welcome_messages"

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_WELCOME_MESSAGES_DICT",
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
        self, INVALID_WELCOME_MESSAGES_DICT: "Mapping[str, object]"
    ) -> None:
        """Test that error is raised when the `welcome_messages` is not a valid value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(INVALID_WELCOME_MESSAGES_DICT, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                exc_info: ExceptionInfo[MessagesJSONFileValueError]
                with pytest.raises(MessagesJSONFileValueError) as exc_info:
                    RuntimeSettings._setup_welcome_messages()  # noqa: SLF001

        assert exc_info.value.dict_key == "welcome_messages"
        assert (
            exc_info.value.invalid_value == INVALID_WELCOME_MESSAGES_DICT["welcome_messages"]
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_MESSAGES_DICT", ({"roles_messages": ["Gaming"]},))
    def test_setup_roles_messages_successful_with_messages_file_path(
        self, TEST_MESSAGES_DICT: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that correct roles messages are loaded when `MESSAGES_FILE_PATH` is valid."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(TEST_MESSAGES_DICT, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                RuntimeSettings._setup_roles_messages()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["ROLES_MESSAGES"] == set(
            TEST_MESSAGES_DICT["roles_messages"],
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_MESSAGES_DICT", ({"roles_messages": ["Gaming"]},))
    def test_setup_roles_messages_successful_with_no_messages_file_path(
        self, TEST_MESSAGES_DICT: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that correct roles messages are loaded when no `MESSAGES_FILE_PATH` given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        DEFAULT_MESSAGES_FILE_PATH: Path = config.PROJECT_ROOT / "messages.json"

        with FileTemporaryDeleter(DEFAULT_MESSAGES_FILE_PATH):
            default_messages_file: TextIO
            with DEFAULT_MESSAGES_FILE_PATH.open("w") as default_messages_file:
                json.dump(TEST_MESSAGES_DICT, fp=default_messages_file)

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                RuntimeSettings._setup_roles_messages()  # noqa: SLF001

            DEFAULT_MESSAGES_FILE_PATH.unlink()

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["ROLES_MESSAGES"] == set(
            TEST_MESSAGES_DICT["roles_messages"],
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("NO_ROLES_MESSAGES_DICT", ({"other_messages": ["Gaming"]},))
    def test_roles_messages_key_not_in_messages_json(
        self, NO_ROLES_MESSAGES_DICT: "Mapping[str, Iterable[str]]"
    ) -> None:
        """Test that error is raised when messages-file not contain `roles_messages` key."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(NO_ROLES_MESSAGES_DICT, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                exc_info: ExceptionInfo[MessagesJSONFileMissingKeyError]
                with pytest.raises(MessagesJSONFileMissingKeyError) as exc_info:
                    RuntimeSettings._setup_roles_messages()  # noqa: SLF001

        assert exc_info.value.missing_key == "roles_messages"

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_ROLES_MESSAGES_DICT",
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
        self, INVALID_ROLES_MESSAGES_DICT: "Mapping[str, object]"
    ) -> None:
        """Test that error is raised when the `roles_messages` is not a valid value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        temporary_messages_file: IO[str]
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temporary_messages_file:
            json.dump(INVALID_ROLES_MESSAGES_DICT, fp=temporary_messages_file)

            temporary_messages_file.close()

            with EnvVariableDeleter("MESSAGES_FILE_PATH"):
                os.environ["MESSAGES_FILE_PATH"] = temporary_messages_file.name

                exc_info: ExceptionInfo[MessagesJSONFileValueError]
                with pytest.raises(MessagesJSONFileValueError) as exc_info:
                    RuntimeSettings._setup_roles_messages()  # noqa: SLF001

        assert exc_info.value.dict_key == "roles_messages"
        assert exc_info.value.invalid_value == INVALID_ROLES_MESSAGES_DICT["roles_messages"]


class TestSetupMembersListURLSessionCookie:
    """Test case to unit-test the `_setup_members_list_auth_session_cookie()` function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_MEMBERS_LIST_URL_SESSION_COOKIE",
        (
            "".join(random.choices(string.hexdigits, k=random.randint(128, 256))),
            f"  {''.join(random.choices(string.hexdigits, k=random.randint(128, 256)))}   ",
        ),
    )
    def test_setup_members_list_auth_session_cookie_successful(
        self, TEST_MEMBERS_LIST_URL_SESSION_COOKIE: str
    ) -> None:
        """
        Test that the given `TEST_MEMBERS_LIST_URL_SESSION_COOKIE` is used when provided.

        In this test, the provided `TEST_MEMBERS_LIST_URL_SESSION_COOKIE` is valid
        and so must be saved successfully.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MEMBERS_LIST_URL_SESSION_COOKIE"):
            os.environ["MEMBERS_LIST_URL_SESSION_COOKIE"] = (
                TEST_MEMBERS_LIST_URL_SESSION_COOKIE
            )

            RuntimeSettings._setup_members_list_auth_session_cookie()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["MEMBERS_LIST_URL_SESSION_COOKIE"] == (
            TEST_MEMBERS_LIST_URL_SESSION_COOKIE.strip()
        )

    def test_missing_members_list_url_session_cookie(self) -> None:
        """Test that an error is raised when no `MEMBERS_LIST_URL_SESSION_COOKIE` is given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MEMBERS_LIST_URL_SESSION_COOKIE"):  # noqa: SIM117
            with pytest.raises(
                ImproperlyConfiguredError,
                match=r"MEMBERS_LIST_URL_SESSION_COOKIE.*valid.*\.ASPXAUTH cookie",
            ):
                RuntimeSettings._setup_members_list_auth_session_cookie()  # noqa: SLF001

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_MEMBERS_LIST_URL_SESSION_COOKIE",
        (
            "INVALID_MEMBERS_LIST_URL_SESSION_COOKIE",
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
    )
    def test_invalid_members_list_url_session_cookie(
        self, INVALID_MEMBERS_LIST_URL_SESSION_COOKIE: str
    ) -> None:
        """Test that an error occurs when `MEMBERS_LIST_URL_SESSION_COOKIE` is invalid."""
        INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE: Final[str] = (
            "MEMBERS_LIST_URL_SESSION_COOKIE must be a valid .ASPXAUTH cookie"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MEMBERS_LIST_URL_SESSION_COOKIE"):
            os.environ["MEMBERS_LIST_URL_SESSION_COOKIE"] = (
                INVALID_MEMBERS_LIST_URL_SESSION_COOKIE
            )

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_MEMBERS_LIST_URL_SESSION_COOKIE_MESSAGE,
            ):
                RuntimeSettings._setup_members_list_auth_session_cookie()  # noqa: SLF001


class TestSetupSendIntroductionReminders:
    """Test case to unit-test the configuration for sending introduction reminders."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_SEND_INTRODUCTION_REMINDERS_VALUE",
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
                    }   ",
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
                                for value in config.VALID_SEND_INTRODUCTION_REMINDERS_VALUES
                                if value.isalpha()
                            ),
                        )
                    ),
                ),
            ),
        ),
    )
    def test_setup_send_introduction_reminders_successful(
        self, TEST_SEND_INTRODUCTION_REMINDERS_VALUE: str
    ) -> None:
        """Test that setup is successful when a valid option is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
            os.environ["SEND_INTRODUCTION_REMINDERS"] = TEST_SEND_INTRODUCTION_REMINDERS_VALUE

            RuntimeSettings._setup_send_introduction_reminders()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["SEND_INTRODUCTION_REMINDERS"] == (
            "once"
            if TEST_SEND_INTRODUCTION_REMINDERS_VALUE.lower().strip() in config.TRUE_VALUES
            else (
                False
                if TEST_SEND_INTRODUCTION_REMINDERS_VALUE.lower().strip()
                not in (
                    "once",
                    "interval",
                )
                else TEST_SEND_INTRODUCTION_REMINDERS_VALUE.lower().strip()
            )
        )

    def test_default_send_introduction_reminders_value(self) -> None:
        """Test that a default value is used when no introduction-reminders-flag is given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
            try:
                RuntimeSettings._setup_send_introduction_reminders()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["SEND_INTRODUCTION_REMINDERS"] in ("once", "interval", False)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_SEND_INTRODUCTION_REMINDERS_VALUE",
        (
            "INVALID_SEND_INTRODUCTION_REMINDERS_VALUE",
            "",
            "  ",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=8),
            ),
        ),
    )
    def test_invalid_send_introduction_reminders(
        self, INVALID_SEND_INTRODUCTION_REMINDERS_VALUE: str
    ) -> None:
        """Test that an error occurs when an invalid introduction-reminders-flag is given."""
        INVALID_SEND_INTRODUCTION_REMINDERS_VALUE_MESSAGE: Final[str] = (
            'SEND_INTRODUCTION_REMINDERS must be one of: "Once", "Interval" or "False"'
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
            os.environ["SEND_INTRODUCTION_REMINDERS"] = (
                INVALID_SEND_INTRODUCTION_REMINDERS_VALUE
            )

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_SEND_INTRODUCTION_REMINDERS_VALUE_MESSAGE,
            ):
                RuntimeSettings._setup_send_introduction_reminders()  # noqa: SLF001

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_SEND_INTRODUCTION_REMINDERS_INTERVAL",
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
    )
    def test_setup_send_introduction_reminders_interval_successful(
        self, TEST_SEND_INTRODUCTION_REMINDERS_INTERVAL: str
    ) -> None:
        """
        Test that the given `SEND_INTRODUCTION_REMINDERS_INTERVAL` is used when provided.

        In this test, the provided `SEND_INTRODUCTION_REMINDERS_INTERVAL` is valid
        and so must be saved successfully.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._setup_send_introduction_reminders()  # noqa: SLF001

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                TEST_SEND_INTRODUCTION_REMINDERS_INTERVAL
            )

            RuntimeSettings._setup_send_introduction_reminders_interval()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["SEND_INTRODUCTION_REMINDERS_INTERVAL"] == {
            key: float(value)
            for key, value in (
                re.match(
                    r"\A(?:(?P<seconds>(?:\d*\.)?\d+)\s*s)?\s*(?:(?P<minutes>(?:\d*\.)?\d+)\s*m)?\s*(?:(?P<hours>(?:\d*\.)?\d+)\s*h)?\Z",
                    TEST_SEND_INTRODUCTION_REMINDERS_INTERVAL.lower().strip(),
                )
                .groupdict()
                .items()  # type: ignore[union-attr]
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
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._setup_send_introduction_reminders()  # noqa: SLF001

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            try:
                RuntimeSettings._setup_send_introduction_reminders_interval()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

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

    def test_setup_send_introduction_reminders_interval_without_send_introduction_reminders_setup(  # noqa: E501
        self,
    ) -> None:
        """Test that an error is raised when setting up the interval without the flag."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        RuntimeSettings._settings.pop("SEND_INTRODUCTION_REMINDERS", None)  # noqa: SLF001

        with pytest.raises(RuntimeError, match="Invalid setup order"):
            RuntimeSettings._setup_send_introduction_reminders_interval()  # noqa: SLF001

    @pytest.mark.parametrize(
        "INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL",
        (
            "INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL",
            "",
            "  ",
            f"{random.randint(1, 999)}d",  # noqa: S311
            f"{random.randint(3, 999)},{random.randint(0, 999)}s",  # noqa: S311
        ),
    )
    def test_invalid_send_introduction_reminders_interval_flag_disabled(
        self, INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL: str
    ) -> None:
        """
        Test that no error is raised when `SEND_INTRODUCTION_REMINDERS_INTERVAL` is invalid.

        The enable/disable flag `SEND_INTRODUCTION_REMINDERS` is disabled (set to `False`)
        during this test, so an invalid interval value should be ignored.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL
            )

            with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
                os.environ["SEND_INTRODUCTION_REMINDERS"] = "false"
                RuntimeSettings._setup_send_introduction_reminders()  # noqa: SLF001

                try:
                    RuntimeSettings._setup_send_introduction_reminders_interval()  # noqa: SLF001
                except ImproperlyConfiguredError:
                    pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL",
        (
            "INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL",
            "",
            "  ",
            f"{random.randint(1, 999)}d",
            f"{random.randint(3, 999)},{random.randint(0, 999)}s",
        ),
    )
    @pytest.mark.parametrize("SEND_INTRODUCTION_REMINDERS_VALUE", ("once", "interval"))
    def test_invalid_send_introduction_reminders_interval_flag_enabled(
        self,
        INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL: str,
        SEND_INTRODUCTION_REMINDERS_VALUE: str,
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

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL
            )

            with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
                os.environ["SEND_INTRODUCTION_REMINDERS"] = random.choice(("once", "interval"))
                RuntimeSettings._setup_send_introduction_reminders()  # noqa: SLF001

                with pytest.raises(
                    ImproperlyConfiguredError,
                    match=INVALID_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE,
                ):
                    RuntimeSettings._setup_send_introduction_reminders_interval()  # noqa: SLF001

    @pytest.mark.parametrize(
        "TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL",
        ("0.5s", "0s", "0.03m", "0m", "0.0005h", "0h"),
    )
    def test_too_small_send_introduction_reminders_interval_flag_disabled(
        self, TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL: str
    ) -> None:
        """
        Test that no error is raised when `SEND_INTRODUCTION_REMINDERS_INTERVAL` is too small.

        The enable/disable flag `SEND_INTRODUCTION_REMINDERS` is disabled (set to `False`)
        during this test, so an invalid interval value should be ignored.
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL
            )

            with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
                os.environ["SEND_INTRODUCTION_REMINDERS"] = "false"
                RuntimeSettings._setup_send_introduction_reminders()  # noqa: SLF001

                try:
                    RuntimeSettings._setup_send_introduction_reminders_interval()  # noqa: SLF001
                except ImproperlyConfiguredError:
                    pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL",
        ("0.5s", "0s", "0.03m", "0m", "0.0005h", "0h"),
    )
    @pytest.mark.parametrize("SEND_INTRODUCTION_REMINDERS_VALUE", ("once", "interval"))
    def test_too_small_send_introduction_reminders_interval_flag_enabled(
        self,
        TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL: str,
        SEND_INTRODUCTION_REMINDERS_VALUE: str,
    ) -> None:
        """
        Test that an error is raised when `SEND_INTRODUCTION_REMINDERS_INTERVAL` is too small.

        The enable/disable flag `SEND_INTRODUCTION_REMINDERS` is enabled
        (set to `once` or `interval`) during this test,
        so an invalid interval value should not be ignored, and an error should be raised.
        """
        TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE: Final[str] = (
            "SEND_INTRODUCTION_REMINDERS_INTERVAL must be greater than 3 seconds"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS_INTERVAL"):
            os.environ["SEND_INTRODUCTION_REMINDERS_INTERVAL"] = (
                TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL
            )

            with EnvVariableDeleter("SEND_INTRODUCTION_REMINDERS"):
                os.environ["SEND_INTRODUCTION_REMINDERS"] = random.choice(("once", "interval"))
                RuntimeSettings._setup_send_introduction_reminders()  # noqa: SLF001

                with pytest.raises(
                    ImproperlyConfiguredError,
                    match=TOO_SMALL_SEND_INTRODUCTION_REMINDERS_INTERVAL_MESSAGE,
                ):
                    RuntimeSettings._setup_send_introduction_reminders_interval()  # noqa: SLF001


class TestSetupSendGetRolesReminders:
    """Test case to unit-test the configuration for sending get-roles reminders."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_SEND_GET_ROLES_REMINDERS_VALUE",
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
        ),
    )
    def test_setup_send_get_roles_reminders_successful(
        self, TEST_SEND_GET_ROLES_REMINDERS_VALUE: str
    ) -> None:
        """Test that setup is successful when a valid option is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS"):
            os.environ["SEND_GET_ROLES_REMINDERS"] = TEST_SEND_GET_ROLES_REMINDERS_VALUE

            RuntimeSettings._setup_send_get_roles_reminders()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["SEND_GET_ROLES_REMINDERS"] == (
            TEST_SEND_GET_ROLES_REMINDERS_VALUE.lower().strip() in config.TRUE_VALUES
        )

    def test_default_send_get_roles_reminders_value(self) -> None:
        """Test that a default value is used when no get-roles-reminders-flag is given."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS"):
            try:
                RuntimeSettings._setup_send_get_roles_reminders()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["SEND_GET_ROLES_REMINDERS"] in (True, False)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_SEND_GET_ROLES_REMINDERS_VALUE",
        (
            "INVALID_SEND_GET_ROLES_REMINDERS_VALUE",
            "",
            "  ",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=8),
            ),
        ),
    )
    def test_invalid_send_get_roles_reminders(
        self, INVALID_SEND_GET_ROLES_REMINDERS_VALUE: str
    ) -> None:
        """Test that an error occurs when an invalid get-roles-reminders-flag is given."""
        INVALID_SEND_GET_ROLES_REMINDERS_VALUE_MESSAGE: Final[str] = (
            "SEND_GET_ROLES_REMINDERS must be a boolean value"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("SEND_GET_ROLES_REMINDERS"):
            os.environ["SEND_GET_ROLES_REMINDERS"] = INVALID_SEND_GET_ROLES_REMINDERS_VALUE

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_SEND_GET_ROLES_REMINDERS_VALUE_MESSAGE
            ):
                RuntimeSettings._setup_send_get_roles_reminders()  # noqa: SLF001


class TestSetupStatisticsDays:
    """Test case to unit-test the `_setup_statistics_days()` function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_STATISTICS_DAYS", ("5", "3.55", "664", "    5   "))
    def test_setup_statistics_days_successful(self, TEST_STATISTICS_DAYS: str) -> None:  # noqa: N803
        """Test that the given valid `STATISTICS_DAYS` is used when one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("STATISTICS_DAYS"):
            os.environ["STATISTICS_DAYS"] = TEST_STATISTICS_DAYS

            RuntimeSettings._setup_statistics_days()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["STATISTICS_DAYS"] == timedelta(
            days=float(TEST_STATISTICS_DAYS.strip()),
        )

    def test_default_statistics_days(self) -> None:
        """Test that a default value is used when no `STATISTICS_DAYS` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("STATISTICS_DAYS"):
            try:
                RuntimeSettings._setup_statistics_days()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert isinstance(RuntimeSettings()["STATISTICS_DAYS"], timedelta)

        assert RuntimeSettings()["STATISTICS_DAYS"] > timedelta(days=1)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_STATISTICS_DAYS",
        (
            "INVALID_STATISTICS_DAYS",
            "",
            "  ",
            "".join(
                random.choices(
                    string.ascii_letters + string.digits + string.punctuation,
                    k=18,
                ),
            ),
        ),
    )
    def test_invalid_statistics_days(self, INVALID_STATISTICS_DAYS: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `STATISTICS_DAYS` is provided."""
        INVALID_STATISTICS_DAYS_MESSAGE: Final[str] = (
            "STATISTICS_DAYS must contain the statistics period in days"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("STATISTICS_DAYS"):
            os.environ["STATISTICS_DAYS"] = INVALID_STATISTICS_DAYS

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_STATISTICS_DAYS_MESSAGE
            ):
                RuntimeSettings._setup_statistics_days()  # noqa: SLF001

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TOO_SMALL_STATISTICS_DAYS",
        ("-15", "-2.3", "-0.02", "0", "0.40", "1"),
    )
    def test_too_small_statistics_days(self, TOO_SMALL_STATISTICS_DAYS: str) -> None:  # noqa: N803
        """Test that an error is raised when a too small `STATISTICS_DAYS` is provided."""
        TOO_SMALL_STATISTICS_DAYS_MESSAGE: Final[str] = (
            r"STATISTICS_DAYS cannot be less than \(or equal to\) 1 day"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("STATISTICS_DAYS"):
            os.environ["STATISTICS_DAYS"] = TOO_SMALL_STATISTICS_DAYS

            with pytest.raises(
                ImproperlyConfiguredError, match=TOO_SMALL_STATISTICS_DAYS_MESSAGE
            ):
                RuntimeSettings._setup_statistics_days()  # noqa: SLF001


class TestSetupStatisticsRoles:
    """Test case to unit-test the `_setup_statistics_roles()` function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_STATISTICS_ROLES",
        (
            "Guest",
            "Guest,Member",
            "Guest,Member,Admin",
            "    Guest,Member,Admin   ",
            "    Guest ,   Member  ,Admin   ",
        ),
    )
    def test_setup_statistics_roles_successful(self, TEST_STATISTICS_ROLES: str) -> None:  # noqa: N803
        """Test that the given valid `STATISTICS_ROLES` is used when they are provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("STATISTICS_ROLES"):
            os.environ["STATISTICS_ROLES"] = TEST_STATISTICS_ROLES

            RuntimeSettings._setup_statistics_roles()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["STATISTICS_ROLES"] == {
            test_statistics_role.strip()
            for test_statistics_role in TEST_STATISTICS_ROLES.strip().split(",")
            if test_statistics_role.strip()
        }

    def test_default_statistics_roles(self) -> None:
        """Test that default values are used when no `STATISTICS_ROLES` are provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("STATISTICS_ROLES"):
            try:
                RuntimeSettings._setup_statistics_roles()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert isinstance(RuntimeSettings()["STATISTICS_ROLES"], Iterable)

        assert bool(RuntimeSettings()["STATISTICS_ROLES"])

        assert all(
            isinstance(statistics_role, str) and bool(statistics_role)
            for statistics_role in RuntimeSettings()["STATISTICS_ROLES"]
        )


class TestSetupModerationDocumentURL:
    """Test case to unit-test the `_setup_moderation_document_url()` function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_MODERATION_DOCUMENT_URL",
        ("https://google.com", "www.google.com/", "    https://google.com   "),
    )
    def test_setup_moderation_document_url_successful(
        self, TEST_MODERATION_DOCUMENT_URL: str
    ) -> None:
        """Test that the given valid `MODERATION_DOCUMENT_URL` is used when one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MODERATION_DOCUMENT_URL"):
            os.environ["MODERATION_DOCUMENT_URL"] = TEST_MODERATION_DOCUMENT_URL

            RuntimeSettings._setup_moderation_document_url()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["MODERATION_DOCUMENT_URL"] == (
            f"https://{TEST_MODERATION_DOCUMENT_URL.strip()}"
            if "://" not in TEST_MODERATION_DOCUMENT_URL.strip()
            else TEST_MODERATION_DOCUMENT_URL.strip()
        )

    def test_missing_moderation_document_url(self) -> None:
        """Test that an error is raised when no `MODERATION_DOCUMENT_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MODERATION_DOCUMENT_URL"):  # noqa: SIM117
            with pytest.raises(
                ImproperlyConfiguredError, match=r"MODERATION_DOCUMENT_URL.*valid.*URL"
            ):
                RuntimeSettings._setup_moderation_document_url()  # noqa: SLF001

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_MODERATION_DOCUMENT_URL",
        ("INVALID_MODERATION_DOCUMENT_URL", "www.google..com/", "", "  "),
    )
    def test_invalid_moderation_document_url(
        self, INVALID_MODERATION_DOCUMENT_URL: str
    ) -> None:
        """Test that an error occurs when the provided `MODERATION_DOCUMENT_URL` is invalid."""
        INVALID_MODERATION_DOCUMENT_URL_MESSAGE: Final[str] = (
            "MODERATION_DOCUMENT_URL must be a valid URL"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MODERATION_DOCUMENT_URL"):
            os.environ["MODERATION_DOCUMENT_URL"] = INVALID_MODERATION_DOCUMENT_URL

            with pytest.raises(
                ImproperlyConfiguredError, match=INVALID_MODERATION_DOCUMENT_URL_MESSAGE
            ):
                RuntimeSettings._setup_moderation_document_url()  # noqa: SLF001


class TestSetupManualModerationWarningMessageLocation:
    """Test case for the `_setup_strike_performed_manually_warning_location()` function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION",
        ("DM", "dm", "general", "Memes", "   general  ", "JUST-CHATTING", "Talking4"),
    )
    def test_setup_strike_performed_manually_warning_location_successful(
        self, TEST_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION: str
    ) -> None:
        """Test that the given valid `MANUAL_MODERATION_WARNING_MESSAGE_LOCATION` is used."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"):
            os.environ["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] = (
                TEST_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION
            )

            RuntimeSettings._setup_strike_performed_manually_warning_location()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] == (
            TEST_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION.upper().strip()
        )

    def test_default_manual_moderation_warning_message_location(self) -> None:
        """Test a default value used when no `MANUAL_MODERATION_WARNING_MESSAGE_LOCATION`."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"):
            try:
                RuntimeSettings._setup_strike_performed_manually_warning_location()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert isinstance(RuntimeSettings()["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"], str)

        assert bool(RuntimeSettings()["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"])

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("INVALID_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION", ("", "  "))
    def test_invalid_manual_moderation_warning_message_location(
        self, INVALID_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION: str
    ) -> None:
        """Test error raised when `MANUAL_MODERATION_WARNING_MESSAGE_LOCATION` is invalid."""
        INVALID_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE: Final[str] = (
            "MANUAL_MODERATION_WARNING_MESSAGE_LOCATION must be a valid name "
            "of a channel in your group's Discord guild."
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"):
            os.environ["MANUAL_MODERATION_WARNING_MESSAGE_LOCATION"] = (
                INVALID_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION
            )

            with pytest.raises(
                ImproperlyConfiguredError,
                match=INVALID_MANUAL_MODERATION_WARNING_MESSAGE_LOCATION_MESSAGE,
            ):
                RuntimeSettings._setup_strike_performed_manually_warning_location()  # noqa: SLF001
