import random
import string
import sys
from argparse import Namespace
from typing import TYPE_CHECKING, Final

import pytest

from tests.test_utils._testing_utils import BaseTestArgumentParser
from utils import UtilityFunction

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture, CaptureResult
    # noinspection PyProtectedMember
    from argparse import _SubParserAction as SubParserAction  # type: ignore[attr-defined]


class TestMain(BaseTestArgumentParser):
    """Test case to unit-test the main argument parser."""

    UTILITY_FUNCTIONS: frozenset[type[UtilityFunction]] = frozenset()

    @classmethod
    def test_error_when_no_function(cls, capsys: "CaptureFixture[str]") -> None:
        """Test for the correct error when no function name is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils: error: the following arguments are required: function"
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function([], capsys)

        assert return_code != 0
        assert not capture_result.out
        assert cls.USAGE_MESSAGE in capture_result.err
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    def test_error_when_invalid_function(cls, capsys: "CaptureFixture[str]") -> None:
        """Test for the correct error when an invalid function name is provided."""
        INVALID_FUNCTION: Final[str] = "".join(
            random.choices(string.ascii_letters + string.digits, k=7)
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils: error: argument function: invalid choice: "
            f"'{INVALID_FUNCTION}' (choose from )"
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            [INVALID_FUNCTION],
            capsys
        )

        assert return_code != 0
        assert not capture_result.out
        assert cls.USAGE_MESSAGE in capture_result.err
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    @pytest.mark.parametrize(
        "help_argument",
        ("test_successful_execution", "test_invalid_function_error_message")
    )
    def test_attaching_utility_function(cls, capsys: "CaptureFixture[str]", help_argument: str) -> None:  # noqa: E501
        """Test for the correct error when an invalid function name is provided."""
        class ExampleUtilityFunction(UtilityFunction):
            NAME: str = "example_utility_function"
            DESCRIPTION: str = "An example utility function for testing purposes"

            @classmethod
            def run(cls, parsed_args: Namespace, parser: "SubParserAction") -> int:  # noqa: ARG003
                sys.stdout.write("Successful execution\n")
                return 0

        return_code: int
        capture_result: CaptureResult[str]

        if help_argument == "test_successful_execution":
            return_code, capture_result = cls.execute_argument_parser_function(
                [ExampleUtilityFunction.NAME],
                capsys,
                {ExampleUtilityFunction}
            )

            assert return_code == 0
            assert not capture_result.err
            assert capture_result.out.strip() == "Successful execution"

        elif help_argument == "test_invalid_function_error_message":
            INVALID_FUNCTION: Final[str] = "".join(
                random.choices(string.ascii_letters + string.digits, k=7)
            )
            EXPECTED_ERROR_MESSAGE: Final[str] = (
                f"utils: error: argument function: invalid choice: "
                f"'{INVALID_FUNCTION}' (choose from {ExampleUtilityFunction.NAME!r})"
            )

            return_code, capture_result = cls.execute_argument_parser_function(
                [INVALID_FUNCTION],
                capsys,
                {ExampleUtilityFunction}
            )

            assert return_code != 0
            assert not capture_result.out
            assert (
                    cls._format_usage_message({ExampleUtilityFunction.NAME})
                    in capture_result.err
            )
            assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    @pytest.mark.parametrize("help_argument", ("-h", "--help"))
    def test_help(cls, capsys: "CaptureFixture[str]", help_argument: str) -> None:
        """Test for the correct response when any of the help arguments are provided."""
        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            [help_argument],
            capsys
        )

        assert return_code == 0
        assert not capture_result.err
        assert cls.USAGE_MESSAGE in capture_result.out
        assert "functions:" in capture_result.out
