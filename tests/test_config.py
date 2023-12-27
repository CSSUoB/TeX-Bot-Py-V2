"""Automated test suite for the `Settings` class & related functions within `config.py`."""

import functools
import logging
import os
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
    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1",))
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
    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1",))
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

    def test_default_log_level(self) -> None:
        """Test that a default value is used when no `CONSOLE_LOG_LEVEL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            RuntimeSettings._setup_logging()  # noqa: SLF001

        assert "texbot" in set(logging.root.manager.loggerDict)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("INVALID_LOG_LEVEL", ("INVALID_LOG_LEVEL",))
    def test_invalid_log_level_env_variable(self, INVALID_LOG_LEVEL: str) -> None:  # noqa: N803
        """Test that an error is raised when an invalid `CONSOLE_LOG_LEVEL` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = INVALID_LOG_LEVEL

            with pytest.raises(ImproperlyConfiguredError, match="LOG_LEVEL must be one of"):
                RuntimeSettings._setup_logging()  # noqa: SLF001

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("LOWERCASE_LOG_LEVEL", ("info",))
    def test_valid_lowercase_log_level_env_variable(self, LOWERCASE_LOG_LEVEL: str) -> None:  # noqa: N803
        """Test that the provided `CONSOLE_LOG_LEVEL` is fixed & used if it is in lowercase."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = LOWERCASE_LOG_LEVEL

            RuntimeSettings._setup_logging()  # noqa: SLF001


class TestSetupDiscordBotToken:
    """Test case to unit-test the `_setup_discord_bot_token()` function."""

    def test_missing_discord_bot_token(self) -> None:
        """Test that an error is raised when no `DISCORD_BOT_TOKEN` is provided."""
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()  # noqa: SLF001

        with EnvVariableDeleter("DISCORD_BOT_TOKEN"):  # noqa: SIM117
            with pytest.raises(ImproperlyConfiguredError, match=r"DISCORD_BOT_TOKEN.*valid.*Discord bot token"):  # noqa: E501
                RuntimeSettings._setup_discord_bot_token()  # noqa: SLF001
