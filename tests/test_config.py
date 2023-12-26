import functools
from collections.abc import Iterable, Callable
from typing import Final

import pytest

from config import Settings, settings


class TestSettings:
    @staticmethod
    def replace_setup_methods(settings_instance: Settings, ignore_methods: Iterable[str] | None = None, replacement_method: Callable[[str], None] | None = None) -> Settings:
        if ignore_methods is None:
            ignore_methods = set()

        def empty_setup_method() -> None:
            pass

        setup_method_name: str
        for setup_method_name in dir(settings_instance):
            if not setup_method_name.startswith("_setup_") or setup_method_name in ignore_methods:
                continue

            setattr(
                settings_instance,
                setup_method_name,
                (
                    functools.partial(replacement_method, setup_method_name=setup_method_name)
                    if replacement_method is not None
                    else empty_setup_method
                )
            )

        return settings_instance

    @pytest.mark.no_independent_settings_instance
    def test_only_single_instance(self) -> None:
        assert id(Settings()) == id(Settings()) == id(settings)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("item_1",))
    def test_get_invalid_settings_key_message(self, TEST_ITEM_NAME: str) -> None:
        assert TEST_ITEM_NAME in Settings.get_invalid_settings_key_message(TEST_ITEM_NAME)
        assert (
                "not a valid settings key"
                in Settings.get_invalid_settings_key_message(TEST_ITEM_NAME)
        )

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getattr_success(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:
        SETTINGS_INSTANCE: Final[Settings] = Settings()
        SETTINGS_INSTANCE._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE
        SETTINGS_INSTANCE._is_env_variables_setup = True

        assert getattr(SETTINGS_INSTANCE, TEST_ITEM_NAME) == TEST_ITEM_VALUE

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("MISSING_ITEM_NAME", ("ITEM",))
    def test_getattr_missing_item(self, MISSING_ITEM_NAME: str) -> None:
        SETTINGS_INSTANCE: Final[Settings] = Settings()
        SETTINGS_INSTANCE._is_env_variables_setup = True

        with pytest.raises(AttributeError, match=Settings.get_invalid_settings_key_message(MISSING_ITEM_NAME)):
            assert getattr(SETTINGS_INSTANCE, MISSING_ITEM_NAME)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1",))
    def test_getattr_invalid_name(self, INVALID_ITEM_NAME: str) -> None:
        SETTINGS_INSTANCE: Final[Settings] = Settings()
        SETTINGS_INSTANCE._is_env_variables_setup = True

        with pytest.raises(AttributeError, match=f"no attribute {INVALID_ITEM_NAME!r}"):
            assert getattr(SETTINGS_INSTANCE, INVALID_ITEM_NAME)

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("TEST_ITEM_NAME", ("ITEM_1",))
    @pytest.mark.parametrize("TEST_ITEM_VALUE", ("value_1",))
    def test_getattr_sets_up_env_variables(self, TEST_ITEM_NAME: str, TEST_ITEM_VALUE: str) -> None:
        is_env_variables_setup: bool = False

        def set_is_env_variables_setup() -> None:
            nonlocal is_env_variables_setup
            is_env_variables_setup = True

        SETTINGS_INSTANCE: Final[Settings] = Settings()
        SETTINGS_INSTANCE._settings[TEST_ITEM_NAME] = TEST_ITEM_VALUE
        SETTINGS_INSTANCE._setup_env_variables = set_is_env_variables_setup

        getattr(SETTINGS_INSTANCE, TEST_ITEM_NAME)

        assert is_env_variables_setup is True

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("MISSING_ITEM_NAME", ("ITEM",))
    def test_getitem_missing_item(self, MISSING_ITEM_NAME: str) -> None:
        SETTINGS_INSTANCE: Final[Settings] = Settings()
        SETTINGS_INSTANCE._is_env_variables_setup = True

        with pytest.raises(KeyError, match=Settings.get_invalid_settings_key_message(MISSING_ITEM_NAME)):
            assert SETTINGS_INSTANCE[MISSING_ITEM_NAME]

    # noinspection PyPep8Naming
    @pytest.mark.parametrize("INVALID_ITEM_NAME", ("item_1",))
    def test_getitem_invalid_name(self, INVALID_ITEM_NAME: str) -> None:
        SETTINGS_INSTANCE: Final[Settings] = Settings()
        SETTINGS_INSTANCE._is_env_variables_setup = True

        with pytest.raises(KeyError, match=str(KeyError(INVALID_ITEM_NAME))):
            assert SETTINGS_INSTANCE[INVALID_ITEM_NAME]

    def test_is_env_variables_setup_made_true(self) -> None:
        SETTINGS_INSTANCE: Final[Settings] = self.replace_setup_methods(
            Settings(),
            ignore_methods=("_setup_env_variables",)
        )

        assert SETTINGS_INSTANCE._is_env_variables_setup is False

        SETTINGS_INSTANCE._setup_env_variables()

        assert SETTINGS_INSTANCE._is_env_variables_setup is True

    def test_every_setup_method_called(self) -> None:
        CALLED_SETUP_METHODS: Final[set[str]] = set()

        def add_called_setup_method(setup_method_name: str) -> None:
            nonlocal CALLED_SETUP_METHODS
            CALLED_SETUP_METHODS.add(setup_method_name)

        SETTINGS_INSTANCE: Final[Settings] = self.replace_setup_methods(
            Settings(),
            ignore_methods=("_setup_env_variables",),
            replacement_method=add_called_setup_method
        )

        SETTINGS_INSTANCE._setup_env_variables()

        assert (
            CALLED_SETUP_METHODS
            == {
                setup_method_name
                for setup_method_name
                in dir(SETTINGS_INSTANCE)
                if (
                    setup_method_name.startswith("_setup_")
                    and setup_method_name != "_setup_env_variables"
                )
            }
        )
