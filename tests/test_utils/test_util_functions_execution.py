"""Automated test suite for the main entrypoint script to execute given util-functions."""

import random
import string
import sys
from argparse import Namespace
from typing import TYPE_CHECKING, Final

import pytest
from classproperties import classproperty

from tests.test_utils._testing_utils import BaseTestArgumentParser
from utils import UtilityFunction

if TYPE_CHECKING:
    from argparse import ArgumentParser

    # noinspection PyProtectedMember
    from argparse import _SubParsersAction as SubParsersAction

    from _pytest.capture import CaptureFixture, CaptureResult


class TestUtilFunctionsExecution(BaseTestArgumentParser):
    """Test case to unit-test the main util-function execution class."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def UTILITY_FUNCTIONS(cls) -> frozenset[type[UtilityFunction]]:  # noqa: N802,N805
        """The set of utility function components associated with this specific test case."""  # noqa: D401
        return frozenset()

    def test_error_when_no_function(self, capsys: "CaptureFixture[str]") -> None:
        """Test for the correct error when no function name is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils: error: the following arguments are required: function"
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = self.execute_argument_parser_function([], capsys)

        assert return_code != 0
        assert not capture_result.out
        assert self.USAGE_MESSAGE in capture_result.err
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    def test_error_when_invalid_function(self, capsys: "CaptureFixture[str]") -> None:
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
        return_code, capture_result = self.execute_argument_parser_function(
            [INVALID_FUNCTION],
            capsys
        )

        assert return_code != 0
        assert not capture_result.out
        assert self.USAGE_MESSAGE in capture_result.err
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @pytest.mark.parametrize(
        "help_argument",
        ("test_successful_execution", "test_invalid_function_error_message")
    )
    def test_attaching_utility_function(self, capsys: "CaptureFixture[str]", help_argument: str) -> None:  # noqa: E501
        """Test for the correct error when an invalid function name is provided."""
        class ExampleUtilityFunction(UtilityFunction):
            NAME: str = "example_utility_function"
            DESCRIPTION: str = "An example utility function for testing purposes"

            @classmethod
            def run(cls, parsed_args: Namespace, parser: "SubParsersAction[ArgumentParser]") -> int:  # noqa: ARG003,E501
                sys.stdout.write("Successful execution\n")
                return 0

        return_code: int
        capture_result: CaptureResult[str]

        if help_argument == "test_successful_execution":
            return_code, capture_result = self.execute_argument_parser_function(
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

            return_code, capture_result = self.execute_argument_parser_function(
                [INVALID_FUNCTION],
                capsys,
                {ExampleUtilityFunction}
            )

            assert return_code != 0
            assert not capture_result.out
            assert (
                    self._format_usage_message({ExampleUtilityFunction.NAME})
                    in capture_result.err
            )
            assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @pytest.mark.parametrize("help_argument", ("-h", "--help"))
    def test_help(self, capsys: "CaptureFixture[str]", help_argument: str) -> None:
        """Test for the correct response when any of the help arguments are provided."""
        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = self.execute_argument_parser_function(
            [help_argument],
            capsys
        )

        assert return_code == 0
        assert not capture_result.err
        assert self.USAGE_MESSAGE in capture_result.out
        assert "functions:" in capture_result.out
