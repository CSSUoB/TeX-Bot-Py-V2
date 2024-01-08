"""Automated test suite for the `Settings` class & related functions within `config.py`."""

import functools
import itertools
import logging
import os
import random
import re
import string
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Final

import pytest

import config
from config import Settings, settings
from exceptions import ImproperlyConfiguredError
from tests._testing_utils import EnvVariableDeleter

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


class TestSettings:
    """Test case to unit-test the `Settings` class & its instances."""

    @staticmethod
    def replace_setup_methods(ignore_methods: Iterable[str] | None = None, replacement_method: Callable[[str], None] | None = None) -> type[Settings]:  # noqa: E501
        """Return a new runtime version of the `Settings` class, with replaced methods."""
        if ignore_methods is None:
            ignore_methods = set()

        def empty_setup_method() -> None:
            pass

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        SETUP_METHOD_NAMES: Final[Iterable[str]] = {
            setup_method_name
            for setup_method_name
            in dir(RuntimeSettings)
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
                    functools.partial(replacement_method, setup_method_name=setup_method_name)
                    if replacement_method is not None
                    else empty_setup_method
                )
            )

        return RuntimeSettings

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("item_1",))
    def test_get_invalid_settings_key_message(self, TEST_ITEM_NAME: str) -> None:  # noqa: N803
        """Test that the `get_invalid_settings_key_message()` method returns correctly."""
        INVALID_SETTINGS_KEY_MESSAGE: Final[str] = settings.get_invalid_settings_key_message(
            TEST_ITEM_NAME
        )

        assert TEST_ITEM_NAME in INVALID_SETTINGS_KEY_MESSAGE
        assert "not a valid settings key" in INVALID_SETTINGS_KEY_MESSAGE

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getattr_success(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:  # noqa: N803
        """Test that retrieving a settings variable by attr-lookup returns the set value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert getattr(RuntimeSettings(), TEST_ITEM_NAME) == TEST_ITEM_VALUE

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("MISSING_ITEM_NAME", ("ITEM",))
    def test_getattr_missing_item(self, MISSING_ITEM_NAME: str) -> None:  # noqa: N803
        """
        Test that requesting a missing settings variable by attribute-lookup raises an error.

        A missing settings variable is one that has a valid name,
        but does not exist within the `_settings` dict (i.e. has not been set).
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        INVALID_SETTINGS_KEY_MESSAGE: Final[str] = (
            RuntimeSettings.get_invalid_settings_key_message(MISSING_ITEM_NAME)
        )

        with pytest.raises(AttributeError, match=INVALID_SETTINGS_KEY_MESSAGE):
            assert getattr(RuntimeSettings(), MISSING_ITEM_NAME)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1", "ITEM__1", "!ITEM_1"))
    def test_getattr_invalid_name(self, INVALID_ITEM_NAME: str) -> None:  # noqa: N803
        """Test that requesting an invalid settings variable by attr-lookup raises an error."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        with pytest.raises(AttributeError, match=f"no attribute {INVALID_ITEM_NAME!r}"):
            assert getattr(RuntimeSettings(), INVALID_ITEM_NAME)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getattr_sets_up_env_variables(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:  # noqa: N803,E501
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

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getitem_success(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:  # noqa: N803
        """Test that retrieving a settings variable by key-lookup returns the set value."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()[TEST_ITEM_NAME] == TEST_ITEM_VALUE

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("MISSING_ITEM_NAME", ("ITEM",))
    def test_getitem_missing_item(self, MISSING_ITEM_NAME: str) -> None:  # noqa: N803
        """
        Test that requesting a missing settings variable by key-lookup raises an error.

        A missing settings variable is one that has a valid name,
        but does not exist within the `_settings` dict (i.e. has not been set).
        """
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        INVALID_SETTINGS_KEY_MESSAGE: Final[str] = (
            RuntimeSettings.get_invalid_settings_key_message(MISSING_ITEM_NAME)
        )

        with pytest.raises(KeyError, match=INVALID_SETTINGS_KEY_MESSAGE):
            assert RuntimeSettings()[MISSING_ITEM_NAME]

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1", "ITEM__1", "!ITEM_1"))
    def test_getitem_invalid_name(self, INVALID_ITEM_NAME: str) -> None:  # noqa: N803
        """Test that requesting an invalid settings variable by key-lookup raises an error."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001
        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        with pytest.raises(KeyError, match=str(KeyError(INVALID_ITEM_NAME))):
            assert RuntimeSettings()[INVALID_ITEM_NAME]

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getitem_sets_up_env_variables(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:  # noqa: N803,E501
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
            ignore_methods=("_setup_env_variables",)
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
            replacement_method=add_called_setup_method
        )

        RuntimeSettings._setup_env_variables()  # noqa: SLF001

        assert (
            CALLED_SETUP_METHODS  # noqa: SIM300
            == {
                setup_method_name
                for setup_method_name
                in dir(RuntimeSettings)
                if (
                    setup_method_name.startswith("_setup_")
                    and setup_method_name != "_setup_env_variables"
                )
            }
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_cannot_setup_more_than_once(self, caplog: "LogCaptureFixture", TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:  # noqa: N803,E501
        """Test that the Env Variables cannot be set more than once."""
        RuntimeSettings: Final[type[Settings]] = self.replace_setup_methods(
            ignore_methods=("_setup_env_variables",)
        )

        RuntimeSettings._setup_env_variables()  # noqa: SLF001
        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE  # noqa: SLF001

        PREVIOUS_SETTINGS: Final[dict[str, object]] = RuntimeSettings._settings.copy()  # noqa: SLF001

        assert not caplog.text

        RuntimeSettings._setup_env_variables()  # noqa: SLF001

        assert RuntimeSettings._settings == PREVIOUS_SETTINGS  # noqa: SLF001
        assert "already" in caplog.text
        assert "set up" in caplog.text


class TestSetupLogging:
    """Test case to unit-test the `_setup_logging()` function."""

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_LOG_LEVEL", ("DEBUG",))
    def test_setup_logging_successful(self, TEST_LOG_LEVEL: str) -> None:  # noqa: N803
        """Test that the given `CONSOLE_LOG_LEVEL` is used when a valid one is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = TEST_LOG_LEVEL

            RuntimeSettings._setup_logging()  # noqa: SLF001

        assert "texbot" in set(logging.root.manager.loggerDict)
        assert (
            logging.getLogger("texbot").getEffectiveLevel()
            == getattr(logging, TEST_LOG_LEVEL)
        )

    def test_default_console_log_level(self) -> None:
        """Test that a default value is used when no `CONSOLE_LOG_LEVEL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            RuntimeSettings._setup_logging()  # noqa: SLF001

        assert "texbot" in set(logging.root.manager.loggerDict)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_LOG_LEVEL",
        (
            "INVALID_LOG_LEVEL",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=18)
            )
        )
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

    @staticmethod
    def get_multiple_random_test_discord_bot_token(*, count: int = 5) -> Iterable[str]:
        """Return `count` number of random test `DISCORD_BOT_TOKEN` values."""
        return (
            f"{
                "".join(
                    random.choices(
                        string.ascii_letters + string.digits,
                        k=random.randint(24, 26)
                    )
                )
            }.{
                "".join(random.choices(string.ascii_letters + string.digits, k=6))
            }.{
                "".join(
                    random.choices(
                        string.ascii_letters + string.digits + "_-",
                        k=random.randint(27, 38)
                    )
                )
            }"
            for _
            in range(count)
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_DISCORD_BOT_TOKEN",
        itertools.chain(
            get_multiple_random_test_discord_bot_token(),
            (f"    {next(iter(get_multiple_random_test_discord_bot_token(count=1)))}   ",)
        )
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
            with pytest.raises(ImproperlyConfiguredError, match=r"DISCORD_BOT_TOKEN.*valid.*Discord bot token"):  # noqa: E501
                RuntimeSettings._setup_discord_bot_token()  # noqa: SLF001

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_DISCORD_BOT_TOKEN",
        (
            "INVALID_DISCORD_BOT_TOKEN",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=18)
            ),
            re.sub(
                r"\A[A-Za-z0-9]{24,26}\.",
                f"{"".join(random.choices(string.ascii_letters + string.digits, k=2))}.",
                string=next(iter(get_multiple_random_test_discord_bot_token(count=1))),
                count=1
            ),
            re.sub(
                r"\A[A-Za-z0-9]{24,26}\.",
                f"{"".join(random.choices(string.ascii_letters + string.digits, k=50))}.",
                string=next(iter(get_multiple_random_test_discord_bot_token(count=1))),
                count=1
            ),
            re.sub(
                r"\A[A-Za-z0-9]{24,26}\.",
                (
                    f"{
                        "".join(random.choices(string.ascii_letters + string.digits, k=12))
                    }>{
                        "".join(random.choices(string.ascii_letters + string.digits, k=12))
                    }."
                ),
                string=next(iter(get_multiple_random_test_discord_bot_token(count=1))),
                count=1
            ),
            re.sub(
                r"\.[A-Za-z0-9]{6}\.",
                f".{"".join(random.choices(string.ascii_letters + string.digits, k=2))}.",
                string=next(iter(get_multiple_random_test_discord_bot_token(count=1))),
                count=1
            ),
            re.sub(
                r"\.[A-Za-z0-9]{6}\.",
                (
                    f".{"".join(random.choices(string.ascii_letters + string.digits, k=50))}."
                ),
                string=next(iter(get_multiple_random_test_discord_bot_token(count=1))),
                count=1
            ),
            re.sub(
                r"\.[A-Za-z0-9]{6}\.",
                (
                    f".{
                        "".join(random.choices(string.ascii_letters + string.digits, k=3))
                    }>{
                        "".join(random.choices(string.ascii_letters + string.digits, k=2))
                    }."
                ),
                string=next(iter(get_multiple_random_test_discord_bot_token(count=1))),
                count=1
            ),
            re.sub(
                r"\.[A-Za-z0-9_-]{27,38}\Z",
                (
                    f".{
                        "".join(
                            random.choices(string.ascii_letters + string.digits + "_-", k=2)
                        )
                    }"
                ),
                string=next(iter(get_multiple_random_test_discord_bot_token(count=1))),
                count=1
            ),
            re.sub(
                r"\.[A-Za-z0-9_-]{27,38}\Z",
                (
                    f".{
                        "".join(
                            random.choices(string.ascii_letters + string.digits + "_-", k=50)
                        )
                    }"
                ),
                string=next(iter(get_multiple_random_test_discord_bot_token(count=1))),
                count=1
            ),
            re.sub(
                r"\.[A-Za-z0-9_-]{27,38}\Z",
                (
                    f".{
                        "".join(
                            random.choices(string.ascii_letters + string.digits + "_-", k=16)
                        )
                    }>{
                        "".join(
                            random.choices(string.ascii_letters + string.digits + "_-", k=16)
                        )
                    }"
                ),
                string=next(iter(get_multiple_random_test_discord_bot_token(count=1))),
                count=1
            )
        )
    )
    def test_invalid_discord_bot_token(self, INVALID_DISCORD_BOT_TOKEN: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `DISCORD_BOT_TOKEN` is provided."""
        INVALID_DISCORD_BOT_TOKEN_MESSAGE: Final[str] = (
            "DISCORD_BOT_TOKEN must be a valid Discord bot token"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_BOT_TOKEN"):
            os.environ["DISCORD_BOT_TOKEN"] = INVALID_DISCORD_BOT_TOKEN

            with pytest.raises(ImproperlyConfiguredError, match=INVALID_DISCORD_BOT_TOKEN_MESSAGE):  # noqa: E501
                RuntimeSettings._setup_discord_bot_token()  # noqa: SLF001


class TestSetupDiscordLogChannelWebhookURL:
    """Test case to unit-test the `_setup_discord_log_channel_webhook_url()` function."""

    @staticmethod
    def get_multiple_random_test_discord_log_channel_webhook_url(count: int = 5, *, with_trailing_slash: bool | None = None) -> Iterable[str]:  # noqa: E501
        """Return `count` number of random test `DISCORD_LOG_CHANNEL_WEBHOOK_URL` values."""
        return (
            f"https://discord.com/api/webhooks/{
                "".join(random.choices(string.digits, k=random.randint(17, 20)))
            }/{
                "".join(
                    random.choices(
                        string.ascii_letters + string.digits,
                        k=random.randint(60, 90)
                    )
                )
            }{
                (
                    "/"
                    if with_trailing_slash
                    else (random.choice(("", "/")) if with_trailing_slash is None else "")
                )
            }"
            for _
            in range(count)
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_DISCORD_LOG_CHANNEL_WEBHOOK_URL",
        itertools.chain(
            get_multiple_random_test_discord_log_channel_webhook_url(
                with_trailing_slash=False
            ),
            get_multiple_random_test_discord_log_channel_webhook_url(
                count=1,
                with_trailing_slash=True
            ),
            (
                (
                    f"    {
                        next(
                            iter(
                                get_multiple_random_test_discord_log_channel_webhook_url(
                                    count=1
                                )
                            )
                        )
                    }   "
                ),
            )
        )
    )
    def test_setup_discord_log_channel_webhook_url_successful(self, TEST_DISCORD_LOG_CHANNEL_WEBHOOK_URL: str) -> None:  # noqa: N803,E501
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

            RuntimeSettings._setup_discord_log_channel_webhook_url()  # noqa: SLF001

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert RuntimeSettings()["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] == (
            TEST_DISCORD_LOG_CHANNEL_WEBHOOK_URL.strip()
        )

    def test_missing_discord_log_channel_webhook_url(self) -> None:
        """Test that no error occurs when no `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_LOG_CHANNEL_WEBHOOK_URL"):
            try:
                RuntimeSettings._setup_discord_log_channel_webhook_url()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert not RuntimeSettings()["DISCORD_LOG_CHANNEL_WEBHOOK_URL"]

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL",
        (
            "INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=18)
            ),
            re.sub(
                r"/\d{17,20}/",
                f"/{"".join(random.choices(string.digits, k=2))}/",
                string=(
                    next(
                        iter(get_multiple_random_test_discord_log_channel_webhook_url(count=1))
                    )
                ),
                count=1
            ),
            re.sub(
                r"/\d{17,20}/",
                f"/{"".join(random.choices(string.digits, k=50))}/",
                string=(
                    next(
                        iter(get_multiple_random_test_discord_log_channel_webhook_url(count=1))
                    )
                ),
                count=1
            ),
            re.sub(
                r"/\d{17,20}/",
                (
                    f"/{
                        "".join(random.choices(string.ascii_letters + string.digits, k=9))
                    }>{
                        "".join(random.choices(string.ascii_letters + string.digits, k=9))
                    }/"
                ),
                string=(
                    next(
                        iter(get_multiple_random_test_discord_log_channel_webhook_url(count=1))
                    )
                ),
                count=1
            ),
            re.sub(
                r"/[a-zA-Z\d]{60,90}",
                f"/{"".join(random.choices(string.ascii_letters + string.digits, k=2))}",
                string=(
                    next(
                        iter(get_multiple_random_test_discord_log_channel_webhook_url(count=1))
                    )
                ),
                count=1
            ),
            re.sub(
                r"/[a-zA-Z\d]{60,90}",
                (
                    f"/{"".join(random.choices(string.ascii_letters + string.digits, k=150))}"
                ),
                string=(
                    next(
                        iter(get_multiple_random_test_discord_log_channel_webhook_url(count=1))
                    )
                ),
                count=1
            ),
            re.sub(
                r"/[a-zA-Z\d]{60,90}",
                (
                    f"/{
                        "".join(random.choices(string.ascii_letters + string.digits, k=37))
                    }>{
                        "".join(random.choices(string.ascii_letters + string.digits, k=37))
                    }"
                ),
                string=(
                    next(
                        iter(get_multiple_random_test_discord_log_channel_webhook_url(count=1))
                    )
                ),
                count=1
            )
        )
    )
    def test_invalid_discord_log_channel_webhook_url(self, INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL: str) -> None:  # noqa: N803,E501
        """Test that an error occurs when `DISCORD_LOG_CHANNEL_WEBHOOK_URL` is invalid."""
        INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE: Final[str] = (
            "DISCORD_LOG_CHANNEL_WEBHOOK_URL must be a valid webhook URL"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_LOG_CHANNEL_WEBHOOK_URL"):
            os.environ["DISCORD_LOG_CHANNEL_WEBHOOK_URL"] = (
                INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL
            )

            with pytest.raises(ImproperlyConfiguredError, match=INVALID_DISCORD_LOG_CHANNEL_WEBHOOK_URL_MESSAGE):  # noqa: E501
                RuntimeSettings._setup_discord_log_channel_webhook_url()  # noqa: SLF001


class TestSetupDiscordGuildID:
    """Test case to unit-test the `_setup_discord_guild_id()` function."""

    @staticmethod
    def get_multiple_random_test_discord_guild_id(count: int = 5) -> Iterable[str]:
        """Return `count` number of random test `DISCORD_GUILD_ID` values."""
        return (
            "".join(random.choices(string.digits, k=random.randint(17, 20)))
            for _
            in range(count)
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "TEST_DISCORD_GUILD_ID",
        itertools.chain(
            get_multiple_random_test_discord_guild_id(),
            (f"    {next(iter(get_multiple_random_test_discord_guild_id(count=1)))}   ",)
        )
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
            with pytest.raises(ImproperlyConfiguredError, match=r"DISCORD_GUILD_ID.*valid.*Discord guild ID"):  # noqa: E501
                RuntimeSettings._setup_discord_guild_id()  # noqa: SLF001

    # noinspection PyPep8Naming
    @pytest.mark.parametrize(
        "INVALID_DISCORD_GUILD_ID",
        (
            "INVALID_DISCORD_GUILD_ID",
            "".join(
                random.choices(string.ascii_letters + string.digits + string.punctuation, k=18)
            ),
            "".join(random.choices(string.digits, k=2)),
            "".join(random.choices(string.digits, k=50))
        )
    )
    def test_invalid_discord_bot_token(self, INVALID_DISCORD_GUILD_ID: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `DISCORD_GUILD_ID` is provided."""
        INVALID_DISCORD_GUILD_ID_MESSAGE: Final[str] = (
            "DISCORD_GUILD_ID must be a valid Discord guild ID"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_GUILD_ID"):
            os.environ["DISCORD_GUILD_ID"] = INVALID_DISCORD_GUILD_ID

            with pytest.raises(ImproperlyConfiguredError, match=INVALID_DISCORD_GUILD_ID_MESSAGE):  # noqa: E501
                RuntimeSettings._setup_discord_guild_id()  # noqa: SLF001


class TestSetupGroupFullName:
    """Test case to unit-test the `_setup_group_full_name()` function."""

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
            "Devil\'s Advocate Society",
            "KASE: Knowledge And Skills Exchange",
            "Law for Non-Law",
            "   Computer Science Society    ",
            "Computer Science Society?",
            "Computer Science Society!",
            "(Computer Science Society)"
        )
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
                for unicode_char, ascii_char
                in zip("‘’´“”–-", "''`\"\"--", strict=True)  # noqa: RUF001
            }
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

    # noinspection PyPep8Naming
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
            "".join(random.choices(string.digits, k=30))
        )
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

    # noinspection PyPep8Naming,SpellCheckingInspection
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
            "(CSS)"
        )
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
                    for unicode_char, ascii_char
                    in zip("‘’´“”–-", "''`\"\"--", strict=True)  # noqa: RUF001
                }
            )
        )

    def test_missing_group_short_name(self) -> None:
        """Test that no error occurs when no `GROUP_SHORT_NAME` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("GROUP_SHORT_NAME"):
            try:
                RuntimeSettings._setup_group_short_name()  # noqa: SLF001
            except ImproperlyConfiguredError:
                pytest.fail(reason="ImproperlyConfiguredError was raised", pytrace=False)

        RuntimeSettings._is_env_variables_setup = True  # noqa: SLF001

        assert not RuntimeSettings()["_GROUP_SHORT_NAME"]

    # noinspection PyPep8Naming
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
            "".join(random.choices(string.digits, k=30))
        )
    )
    def test_invalid_group_short_name(self, INVALID_GROUP_SHORT_NAME: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `GROUP_SHORT_NAME` is provided."""
        INVALID_GROUP_SHORT_NAME_MESSAGE: Final[str] = (
            "GROUP_SHORT_NAME must not contain any invalid characters"
        )

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("GROUP_SHORT_NAME"):
            os.environ["GROUP_SHORT_NAME"] = INVALID_GROUP_SHORT_NAME

            with pytest.raises(ImproperlyConfiguredError, match=INVALID_GROUP_SHORT_NAME_MESSAGE):  # noqa: E501
                RuntimeSettings._setup_group_short_name()  # noqa: SLF001
