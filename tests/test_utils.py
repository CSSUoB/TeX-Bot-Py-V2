"""Test suite for utils.py."""

import os
import random
import re
import string
import sys
from argparse import Namespace
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Final

import pytest
from _pytest.capture import CaptureFixture, CaptureResult

import utils
from utils import InviteURLGenerator, UtilityFunction, classproperty


class TestInviteURLGenerator:
    """Test case to unit-test the low-level URL generation function."""

    @staticmethod
    def test_url_generates() -> None:
        """Test that the invite URL generates successfully when valid arguments are passed."""
        DISCORD_BOT_APPLICATION_ID: Final[str] = "".join(
            random.choices(string.digits, k=random.randint(17, 20))
        )
        DISCORD_GUILD_ID: Final[int] = random.randint(
            10000000000000000,
            99999999999999999999
        )

        invite_url: str = InviteURLGenerator.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID,
            DISCORD_GUILD_ID
        )

        assert re.match(
            f"https://discord.com/.*={DISCORD_BOT_APPLICATION_ID}.*={DISCORD_GUILD_ID}",
            invite_url
        )


# TODO(CarrotManMatt): Move to stats_tests  # noqa: FIX002
# https://github.com/CSSUoB/TeX-Bot-Py-V2/issues/57
# class TestPlotBarChart:
#     """Test case to unit-test the plot_bar_chart function."""
#
#     def test_bar_chart_generates(self) -> None:
#         """Test that the bar chart generates successfully when valid arguments are passed."""  # noqa: ERA001, E501, W505
#         FILENAME: Final[str] = "output_chart.png"  # noqa: ERA001
#         DESCRIPTION: Final[str] = "Bar chart of the counted value of different roles."  # noqa: ERA001, E501, W505
#
#         bar_chart_image: discord.File = plot_bar_chart(
#             data={"role1": 5, "role2": 7},  # noqa: ERA001
#             x_label="Role Name",  # noqa: ERA001
#             y_label="Counted value",  # noqa: ERA001
#             title="Counted Value Of Each Role",  # noqa: ERA001
#             filename=FILENAME,  # noqa: ERA001
#             description=DESCRIPTION,  # noqa: ERA001
#             extra_text="This is extra text"  # noqa: ERA001
#         )  # noqa: ERA001, RUF100
#
#         assert bar_chart_image.filename == FILENAME  # noqa: ERA001
#         assert bar_chart_image.description == DESCRIPTION  # noqa: ERA001
#         assert bool(bar_chart_image.fp.read()) is True  # noqa: ERA001


# TODO(CarrotManMatt): Move to stats_tests  # noqa: FIX002
# https://github.com/CSSUoB/TeX-Bot-Py-V2/issues/57
# class TestAmountOfTimeFormatter:
#     """Test case to unit-test the amount_of_time_formatter function."""
#
#     @pytest.mark.parametrize(
#         "time_value",
#         (1, 1.0, 0.999999, 1.000001)  # noqa: ERA001
#     )  # noqa: ERA001, RUF100
#     def test_format_unit_value(self, time_value: float) -> None:
#         """Test that a value of one only includes the time_scale."""
#         TIME_SCALE: Final[str] = "day"  # noqa: ERA001
#
#         formatted_amount_of_time: str = amount_of_time_formatter(time_value, TIME_SCALE)  # noqa: ERA001, E501, W505
#
#         assert formatted_amount_of_time == TIME_SCALE  # noqa: ERA001
#         assert not formatted_amount_of_time.endswith("s")  # noqa: ERA001
#
#     # noinspection PyTypeChecker
#     @pytest.mark.parametrize(
#         "time_value",
#         (*range(2, 21), 2.00, 0, 0.0, 25.0, -0, -0.0, -25.0)  # noqa: ERA001
#     )  # noqa: ERA001, RUF100
#     def test_format_integer_value(self, time_value: float) -> None:
#         """Test that an integer value includes the value and time_scale pluralized."""
#         TIME_SCALE: Final[str] = "day"  # noqa: ERA001
#
#         assert utils.amount_of_time_formatter(
#             time_value,
#             TIME_SCALE
#         ) == f"{int(time_value)} {TIME_SCALE}s"
#
#     @pytest.mark.parametrize("time_value", (3.14159, 0.005, 25.0333333))
#     def test_format_float_value(self, time_value: float) -> None:
#         """Test that a float value includes the rounded value and time_scale pluralized."""
#         TIME_SCALE: Final[str] = "day"  # noqa: ERA001
#
#         assert utils.amount_of_time_formatter(
#             time_value,
#             TIME_SCALE
#         ) == f"{time_value:.2f} {TIME_SCALE}s"


class BaseTestArgumentParser:
    """Parent class to define the execution code used by all ArgumentParser test cases."""

    INITIAL_EXECUTED_COMMAND: Final[str] = Path(sys.argv[0]).name
    UTILITY_FUNCTIONS: frozenset[UtilityFunction]

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def USAGE_MESSAGE(cls) -> str:  # noqa: N805,N802
        """The error message describing how the given function should be called."""  # noqa: D401
        return cls._format_usage_message(
            utility_function.NAME for utility_function in cls.UTILITY_FUNCTIONS
        )

    @classmethod
    def _format_usage_message(cls, utility_function_names: Iterable[str]) -> str:
        return f"""usage: {cls.INITIAL_EXECUTED_COMMAND} [-h]{
            " {" if utility_function_names else ""
        }{"|".join(utility_function_names)}{
            "}" if utility_function_names else ""
        }"""

    @classmethod
    def execute_argument_parser_function(cls, args: Sequence[str], capsys: CaptureFixture[str], utility_functions: Iterable[UtilityFunction] | None = None) -> tuple[int, CaptureResult[str]]:  # noqa: E501
        """Execute the chosen argument parser function."""
        try:
            return_code: int = utils.main(
                args,
                cls.UTILITY_FUNCTIONS if utility_functions is None else utility_functions
            )
        except SystemExit as e:
            return_code = 0 if not e.code else int(e.code)

        return return_code, capsys.readouterr()


class TestMain(BaseTestArgumentParser):
    """Test case to unit-test the main argument parser."""

    UTILITY_FUNCTIONS: frozenset[UtilityFunction] = frozenset()

    @classmethod
    def test_error_when_no_function(cls, capsys: CaptureFixture[str]) -> None:
        """Test for the correct error when no function name is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            f"{cls.INITIAL_EXECUTED_COMMAND}: error: "
            "the following arguments are required: function"
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function([], capsys)

        assert return_code != 0
        assert not capture_result.out
        assert cls.USAGE_MESSAGE in capture_result.err
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    def test_error_when_invalid_function(cls, capsys: CaptureFixture[str]) -> None:
        """Test for the correct error when an invalid function name is provided."""
        INVALID_FUNCTION: Final[str] = "".join(
            random.choices(string.ascii_letters + string.digits, k=7)
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            f"{cls.INITIAL_EXECUTED_COMMAND}: error: argument function: invalid choice: "
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
    def test_attaching_utility_function(cls, capsys: CaptureFixture[str], help_argument: str) -> None:  # noqa: E501
        """Test for the correct error when an invalid function name is provided."""
        class ExampleUtilityFunction(UtilityFunction):
            NAME: str = "example_utility_function"
            DESCRIPTION: str = "An example utility function for testing purposes"

            def run(self, parsed_args: Namespace) -> int:  # noqa: ARG002
                sys.stdout.write("Successful execution\n")
                return 0

        return_code: int
        capture_result: CaptureResult[str]

        if help_argument == "test_successful_execution":
            return_code, capture_result = cls.execute_argument_parser_function(
                [ExampleUtilityFunction.NAME],
                capsys,
                {ExampleUtilityFunction()}
            )

            assert return_code == 0
            assert not capture_result.err
            assert capture_result.out == "Successful execution\n"

        elif help_argument == "test_invalid_function_error_message":
            INVALID_FUNCTION: Final[str] = "".join(
                random.choices(string.ascii_letters + string.digits, k=7)
            )
            EXPECTED_ERROR_MESSAGE: Final[str] = (
                f"{cls.INITIAL_EXECUTED_COMMAND}: error: argument function: invalid choice: "
                f"'{INVALID_FUNCTION}' (choose from {ExampleUtilityFunction.NAME!r})"
            )

            return_code, capture_result = cls.execute_argument_parser_function(
                [INVALID_FUNCTION],
                capsys,
                {ExampleUtilityFunction()}
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
    def test_help(cls, capsys: CaptureFixture[str], help_argument: str) -> None:
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


class TestGenerateInviteURLArgumentParser(BaseTestArgumentParser):
    """Test case to unit-test the generate_invite_url argument parser."""

    @classmethod
    def execute_util_function(cls, util_function_name: str, *arguments: str, delete_env_guild_id: bool = True) -> None:  # noqa: E501
        """
        Execute the given utility function.

        The command line outputs are stored in class variables for later access.
        """
        PROJECT_ROOT: Final[Path] = cls._get_project_root()
        env_file_path: Path = PROJECT_ROOT / Path(".env")
        if env_file_path.is_file():
            env_file_path = env_file_path.rename(PROJECT_ROOT / Path("._env"))

        old_env_discord_guild_id: str | None = os.environ.get("DISCORD_GUILD_ID")
        if delete_env_guild_id and old_env_discord_guild_id is not None:
            del os.environ["DISCORD_GUILD_ID"]

        super().execute_util_function(util_function_name, *arguments)

        if delete_env_guild_id and old_env_discord_guild_id is not None:
            os.environ["DISCORD_GUILD_ID"] = old_env_discord_guild_id

        if env_file_path.is_file():
            env_file_path.rename(PROJECT_ROOT / Path(".env"))

    @classmethod
    def test_url_generates_without_discord_guild_id_environment_variable(cls) -> None:
        """Test for the correct response when discord_guild_id is given as an env variable."""
        DISCORD_BOT_APPLICATION_ID: Final[str] = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        DISCORD_GUILD_ID: Final[int] = random.randint(
            10000000000000000,
            99999999999999999999
        )

        old_env_discord_guild_id: str = os.environ.get("DISCORD_GUILD_ID", "")
        os.environ["DISCORD_GUILD_ID"] = str(DISCORD_GUILD_ID)

        cls.execute_util_function(
            "generate_invite_url",
            DISCORD_BOT_APPLICATION_ID,
            delete_env_guild_id=False
        )

        if old_env_discord_guild_id:
            os.environ["DISCORD_GUILD_ID"] = old_env_discord_guild_id
        else:
            del os.environ["DISCORD_GUILD_ID"]

        assert cls.parser_output_return_code == 0
        assert not cls.parser_output_stderr
        assert cls.parser_output_stdout == InviteURLGenerator.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID,
            DISCORD_GUILD_ID
        )

    @classmethod
    def test_url_generates_with_discord_guild_id_environment_variable(cls) -> None:
        """Test for the correct response when discord_guild_id is provided as an argument."""
        DISCORD_BOT_APPLICATION_ID: Final[str] = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        DISCORD_GUILD_ID: Final[int] = random.randint(
            10000000000000000,
            99999999999999999999
        )

        cls.execute_util_function(
            "generate_invite_url",
            DISCORD_BOT_APPLICATION_ID,
            str(DISCORD_GUILD_ID)
        )

        assert cls.parser_output_return_code == 0
        assert not cls.parser_output_stderr
        assert cls.parser_output_stdout == InviteURLGenerator.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID,
            DISCORD_GUILD_ID
        )

    @classmethod
    def test_error_when_no_discord_bot_application_id(cls) -> None:
        """Test for the correct error when no discord_bot_application_id is provided."""
        EXPECTED_USAGE_MESSAGE: Final[str] = (
            "usage: utils.py generate_invite_url [-h] "
            "discord_bot_application_id [discord_guild_id]"
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils.py generate_invite_url: error: the following arguments are required: "
            "discord_bot_application_id"
        )
        cls.execute_util_function(util_function_name="generate_invite_url")

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert EXPECTED_USAGE_MESSAGE in cls.parser_output_stderr
        assert EXPECTED_ERROR_MESSAGE in cls.parser_output_stderr

    @classmethod
    def test_error_when_invalid_discord_bot_application_id(cls) -> None:
        """Test for the correct error with an invalid discord_bot_application_id."""
        EXPECTED_USAGE_MESSAGE: Final[str] = (
            "usage: utils.py generate_invite_url [-h] "
            "discord_bot_application_id [discord_guild_id]"
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils.py generate_invite_url: error: discord_bot_application_id must be "
            "a valid Discord application ID "
            "(see https://support-dev.discord.com/hc/en-gb/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-)"
        )

        cls.execute_util_function(
            "generate_invite_url",
            "".join(
                random.choices(string.ascii_letters + string.digits, k=7)
            )
        )

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert EXPECTED_USAGE_MESSAGE in cls.parser_output_stderr
        assert EXPECTED_ERROR_MESSAGE in cls.parser_output_stderr

    @classmethod
    def test_error_when_no_discord_guild_id(cls) -> None:
        """Test for the correct error when no discord_guild_id is provided."""
        EXPECTED_USAGE_MESSAGE: Final[str] = (
            "usage: utils.py generate_invite_url [-h] "
            "discord_bot_application_id [discord_guild_id]"
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils.py generate_invite_url: error: discord_guild_id must be provided as an "
            "argument to the generate_invite_url utility function or otherwise set "
            "the DISCORD_GUILD_ID environment variable"
        )

        cls.execute_util_function(
            "generate_invite_url",
            "".join(
                random.choices(string.digits, k=random.randint(17, 20))
            )
        )

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert EXPECTED_USAGE_MESSAGE in cls.parser_output_stderr
        assert EXPECTED_ERROR_MESSAGE in cls.parser_output_stderr

    @classmethod
    def test_error_when_invalid_discord_guild_id(cls) -> None:
        """Test for the correct error when an invalid discord_guild_id is provided."""
        EXPECTED_USAGE_MESSAGE: Final[str] = (
            "usage: utils.py generate_invite_url [-h] "
            "discord_bot_application_id [discord_guild_id]"
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils.py generate_invite_url: error: discord_guild_id must be "
            "a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
        )

        cls.execute_util_function(
            "generate_invite_url",
            str(
                random.randint(10000000000000000, 99999999999999999999)
            ),
            "".join(
                random.choices(string.ascii_letters + string.digits, k=7)
            )
        )

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert EXPECTED_USAGE_MESSAGE in cls.parser_output_stderr
        assert EXPECTED_ERROR_MESSAGE in cls.parser_output_stderr

    @classmethod
    def test_error_when_too_many_arguments(cls) -> None:
        """Test for the correct error when too many arguments are provided."""
        EXTRA_ARGUMENT: Final[str] = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils.py: error: "
            f"unrecognized arguments: {EXTRA_ARGUMENT}"
        )

        cls.execute_util_function(
            "generate_invite_url",
            str(
                random.randint(10000000000000000, 99999999999999999999)
            ),
            str(
                random.randint(10000000000000000, 99999999999999999999)
            ),
            EXTRA_ARGUMENT
        )

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stderr
        assert EXPECTED_ERROR_MESSAGE in cls.parser_output_stderr
