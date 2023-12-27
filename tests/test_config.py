import functools
import logging
import os
from collections.abc import Iterable, Callable
from typing import Final, TYPE_CHECKING

import pytest

import config
from tests._testing_utils import EnvVariableDeleter
from config import Settings, settings
from exceptions import ImproperlyConfiguredError

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


class TestSettings:
    @staticmethod
    def replace_setup_methods(ignore_methods: Iterable[str] | None = None, replacement_method: Callable[[str], None] | None = None) -> type[Settings]:
        if ignore_methods is None:
            ignore_methods = set()

        def empty_setup_method() -> None:
            pass

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

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
    def test_get_invalid_settings_key_message(self, TEST_ITEM_NAME: str) -> None:
        INVALID_SETTINGS_KEY_MESSAGE: Final[str] = settings.get_invalid_settings_key_message(
            TEST_ITEM_NAME
        )

        assert TEST_ITEM_NAME in INVALID_SETTINGS_KEY_MESSAGE
        assert "not a valid settings key" in INVALID_SETTINGS_KEY_MESSAGE

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getattr_success(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE
        RuntimeSettings._is_env_variables_setup = True

        assert getattr(RuntimeSettings(), TEST_ITEM_NAME) == TEST_ITEM_VALUE

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("MISSING_ITEM_NAME", ("ITEM",))
    def test_getattr_missing_item(self, MISSING_ITEM_NAME: str) -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        RuntimeSettings._is_env_variables_setup = True

        with pytest.raises(AttributeError, match=RuntimeSettings.get_invalid_settings_key_message(MISSING_ITEM_NAME)):
            assert getattr(RuntimeSettings(), MISSING_ITEM_NAME)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1",))
    def test_getattr_invalid_name(self, INVALID_ITEM_NAME: str) -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        RuntimeSettings._is_env_variables_setup = True

        with pytest.raises(AttributeError, match=f"no attribute {INVALID_ITEM_NAME!r}"):
            assert getattr(RuntimeSettings(), INVALID_ITEM_NAME)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getattr_sets_up_env_variables(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:
        is_env_variables_setup: bool = False

        def set_is_env_variables_setup(_instance: Settings | None = None) -> None:
            nonlocal is_env_variables_setup
            is_env_variables_setup = True

        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE
        RuntimeSettings._setup_env_variables = set_is_env_variables_setup

        getattr(RuntimeSettings(), TEST_ITEM_NAME)

        assert is_env_variables_setup is True

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("MISSING_ITEM_NAME", ("ITEM",))
    def test_getitem_missing_item(self, MISSING_ITEM_NAME: str) -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._is_env_variables_setup = True

        with pytest.raises(KeyError, match=RuntimeSettings.get_invalid_settings_key_message(MISSING_ITEM_NAME)):
            assert RuntimeSettings()[MISSING_ITEM_NAME]

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1",))
    def test_getitem_invalid_name(self, INVALID_ITEM_NAME: str) -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()
        RuntimeSettings._is_env_variables_setup = True

        with pytest.raises(KeyError, match=str(KeyError(INVALID_ITEM_NAME))):
            assert RuntimeSettings()[INVALID_ITEM_NAME]

    def test_is_env_variables_setup_made_true(self) -> None:
        RuntimeSettings: Final[type[Settings]] = self.replace_setup_methods(
            ignore_methods=("_setup_env_variables",)
        )

        assert RuntimeSettings._is_env_variables_setup is False

        RuntimeSettings._setup_env_variables()

        assert RuntimeSettings._is_env_variables_setup is True

    def test_every_setup_method_called(self) -> None:
        CALLED_SETUP_METHODS: Final[set[str]] = set()

        def add_called_setup_method(setup_method_name: str) -> None:
            nonlocal CALLED_SETUP_METHODS
            CALLED_SETUP_METHODS.add(setup_method_name)

        RuntimeSettings: Final[type[Settings]] = self.replace_setup_methods(
            ignore_methods=("_setup_env_variables",),
            replacement_method=add_called_setup_method
        )

        RuntimeSettings._setup_env_variables()

        assert (
            CALLED_SETUP_METHODS
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

    def test_cannot_setup_multiple_times(self, caplog: "LogCaptureFixture") -> None:
        RuntimeSettings: Final[type[Settings]] = self.replace_setup_methods(
            ignore_methods=("_setup_env_variables",)
        )

        RuntimeSettings._setup_env_variables()

        assert not caplog.text

        RuntimeSettings._setup_env_variables()

        assert "already" in caplog.text and "set up" in caplog.text


class TestSetupLogging:
    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_LOG_LEVEL", ("DEBUG",))
    def test_setup_logging_successful(self, TEST_LOG_LEVEL: str) -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = TEST_LOG_LEVEL

            RuntimeSettings._setup_logging()

        assert "texbot" in set(logging.root.manager.loggerDict)
        assert (
            logging.getLogger("texbot").getEffectiveLevel()
            == getattr(logging, TEST_LOG_LEVEL)
        )

    def test_default_log_level(self, caplog: "LogCaptureFixture") -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            RuntimeSettings._setup_logging()

        assert "texbot" in set(logging.root.manager.loggerDict)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("INVALID_LOG_LEVEL", ("INVALID_LOG_LEVEL",))
    def test_invalid_log_level_env_variable(self, INVALID_LOG_LEVEL: str) -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = INVALID_LOG_LEVEL

            with pytest.raises(ImproperlyConfiguredError, match="LOG_LEVEL must be one of"):
                RuntimeSettings._setup_logging()

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("LOWERCASE_LOG_LEVEL", ("info",))
    def test_valid_lowercase_log_level_env_variable(self, LOWERCASE_LOG_LEVEL: str) -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("CONSOLE_LOG_LEVEL"):
            os.environ["CONSOLE_LOG_LEVEL"] = LOWERCASE_LOG_LEVEL

            RuntimeSettings._setup_logging()


class TestSetupDiscordBotToken:
    def test_missing_discord_bot_token(self) -> None:
        RuntimeSettings: Final[type[Settings]] = config._settings_class_factory()

        with EnvVariableDeleter("DISCORD_BOT_TOKEN"):
            with pytest.raises(ImproperlyConfiguredError, match=r"DISCORD_BOT_TOKEN.*valid.*Discord bot token"):  # noqa: E501
                RuntimeSettings._setup_discord_bot_token()
