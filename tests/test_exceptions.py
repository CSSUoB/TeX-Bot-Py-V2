from typing import Final

import pytest
from classproperties import classproperty

from exceptions import BaseDoesNotExistError, BaseTeXBotError, ImproperlyConfiguredError


class TestImproperlyConfiguredError:
    def test_message(self) -> None:
        TEST_EXCEPTION_MESSAGE: Final[str] = "Test error occurred"

        assert str(ImproperlyConfiguredError(TEST_EXCEPTION_MESSAGE)) == TEST_EXCEPTION_MESSAGE

    def test_message_when_raised(self) -> None:
        TEST_EXCEPTION_MESSAGE: Final[str] = "Test error occurred"

        with pytest.raises(ImproperlyConfiguredError, match=TEST_EXCEPTION_MESSAGE):
            raise ImproperlyConfiguredError(TEST_EXCEPTION_MESSAGE)


class TestBaseTeXBotError:
    class _DefaultMessageBaseTeXBotErrorSubclass(BaseTeXBotError):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
            return "Test error occurred"

    class _AttributesBaseTeXBotErrorSubclass(_DefaultMessageBaseTeXBotErrorSubclass):
        def __init__(self, message: str | None = None, test_attribute_value: object | None = None) -> None:
            """Initialize a new exception with the given error message."""
            self.test_attribute: object | None = test_attribute_value

            super().__init__(message=message)

    @pytest.mark.parametrize(
        "test_base_texbot_error_subclass",
        (
            _DefaultMessageBaseTeXBotErrorSubclass(),
            _DefaultMessageBaseTeXBotErrorSubclass(message=None),
            _DefaultMessageBaseTeXBotErrorSubclass(message="")
        )
    )
    def test_default_message(self, test_base_texbot_error_subclass: BaseTeXBotError) -> None:
        assert (
            test_base_texbot_error_subclass.message
            == self._DefaultMessageBaseTeXBotErrorSubclass.DEFAULT_MESSAGE
        )
        assert (
            str(test_base_texbot_error_subclass)
            == self._DefaultMessageBaseTeXBotErrorSubclass.DEFAULT_MESSAGE
        )

    def test_custom_message(self) -> None:
        TEST_EXCEPTION_MESSAGE: Final[str] = "Other test error occurred"

        assert (
            self._DefaultMessageBaseTeXBotErrorSubclass(TEST_EXCEPTION_MESSAGE).message
            == TEST_EXCEPTION_MESSAGE
        )
        assert (
            str(self._DefaultMessageBaseTeXBotErrorSubclass(TEST_EXCEPTION_MESSAGE))
            == TEST_EXCEPTION_MESSAGE
        )

    @pytest.mark.parametrize(
        "test_attributes_base_texbot_error_subclass",
        (
            _AttributesBaseTeXBotErrorSubclass(),
            _AttributesBaseTeXBotErrorSubclass(test_attribute_value=None),
            _AttributesBaseTeXBotErrorSubclass(test_attribute_value=7)
        )
    )
    def test_repr_with_attributes(self, test_attributes_base_texbot_error_subclass: _AttributesBaseTeXBotErrorSubclass) -> None:
        assert (
            f"test_attribute={test_attributes_base_texbot_error_subclass.test_attribute!r}"
            in repr(test_attributes_base_texbot_error_subclass)
        )


class TestBaseErrorWithErrorCode:
    """"""


class TestBaseDoesNotExistError:
    class _NoDependantsBaseDoesNotExistErrorSubclass(BaseDoesNotExistError):
        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DEFAULT_MESSAGE(self) -> str:  # noqa: N805,N802
            return "Test error occurred"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def ERROR_CODE(self) -> str:  # noqa: N805,N802
            return "E1"

        # noinspection PyMethodParameters,PyPep8Naming
        @classproperty
        def DOES_NOT_EXIST_TYPE(self) -> str:  # noqa: N805,N802
            return "test_object_type"

    def test_get_formatted_message_with_no_dependants(self) -> None:
        with pytest.raises(ValueError, match="no dependants"):
            self._NoDependantsBaseDoesNotExistErrorSubclass.get_formatted_message(
                non_existent_object_identifier="object_1"
            )
