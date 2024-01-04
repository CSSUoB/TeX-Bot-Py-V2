"""Test suite for utils package."""

from collections.abc import Sequence

__all__: Sequence[str] = ()

import os
import random
import re
import string
import sys
from argparse import Namespace
from collections.abc import Iterable, Sequence
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Final

import pytest
from _pytest.capture import CaptureFixture, CaptureResult
from classproperties import classproperty

import utils
from utils import InviteURLGenerator, UtilityFunction

if TYPE_CHECKING:
    from argparse import ArgumentParser
    # noinspection PyProtectedMember
    from argparse import _SubParsersAction as SubParsersAction

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
#     @pytest.mark.parametrize(
#         "time_value",
#         (*range(2, 21), 2.00, 0, 0.0, 25.0, -0, -0.0, -25.0)  # noqa: ERA001
#     )  # noqa: ERA001, RUF100
#     def test_format_integer_value(self, time_value: float) -> None:
#         """Test that an integer value includes the value and time_scale pluralized."""
#         TIME_SCALE: Final[str] = "day"  # noqa: ERA001
#
#         assert amount_of_time_formatter(
#             time_value,
#             TIME_SCALE
#         ) == f"{int(time_value)} {TIME_SCALE}s"
#
#     @pytest.mark.parametrize("time_value", (3.14159, 0.005, 25.0333333))
#     def test_format_float_value(self, time_value: float) -> None:
#         """Test that a float value includes the rounded value and time_scale pluralized."""
#         TIME_SCALE: Final[str] = "day"  # noqa: ERA001
#
#         assert amount_of_time_formatter(
#             time_value,
#             TIME_SCALE
#         ) == f"{time_value:.2f} {TIME_SCALE}s"


class BaseTestArgumentParser:
    """Parent class to define the execution code used by all ArgumentParser test cases."""

    UTILITY_FUNCTIONS: frozenset[type[UtilityFunction]]

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def USAGE_MESSAGE(cls) -> str:  # noqa: N805,N802
        """The error message describing how the given function should be called."""  # noqa: D401
        return cls._format_usage_message(
            utility_function.NAME for utility_function in cls.UTILITY_FUNCTIONS
        )

    @classmethod
    def _format_usage_message(cls, utility_function_names: Iterable[str]) -> str:
        return f"""usage: utils [-h]{
            " {" if utility_function_names else ""
        }{
            "|".join(utility_function_names)
        }{
            "}" if utility_function_names else ""
        }"""

    @classmethod
    def execute_argument_parser_function(cls, args: Sequence[str], capsys: CaptureFixture[str], utility_functions: Iterable[type[UtilityFunction]] | None = None) -> tuple[int, CaptureResult[str]]:  # noqa: E501
        """Execute the chosen argument parser function."""
        try:
            return_code: int = utils.main(
                args,
                cls.UTILITY_FUNCTIONS if utility_functions is None else utility_functions
            )
        except SystemExit as e:
            return_code = 0 if not e.code else int(e.code)

        return return_code, capsys.readouterr()

    class EmptyContextManager:
        """Empty context manager that executes no logic when entering/exiting."""

        def __enter__(self) -> None:
            """Enter the context manager and execute no additional logic."""

        def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType) -> None:  # noqa: E501
            """Exit the context manager and execute no additional logic."""

    class EnvVariableDeleter(EmptyContextManager):
        """
        Context manager that deletes the given environment variable.

        The given environment variable is removed from both
        the system environment variables list,
        and the .env file in this project's root directory.
        """

        @staticmethod
        def _get_project_root() -> Path:
            project_root: Path = Path(__file__).resolve()

            for _ in range(8):
                project_root = project_root.parent

                if any(path.name.startswith("README.md") for path in project_root.iterdir()):
                    return project_root

            NO_ROOT_DIRECTORY_MESSAGE: Final[str] = "Could not locate project root directory."
            raise FileNotFoundError(NO_ROOT_DIRECTORY_MESSAGE)

        def __init__(self, env_variable_name: str) -> None:
            """Store the current state of any instances of the stored environment variable."""
            self.env_variable_name: str = env_variable_name
            self.PROJECT_ROOT: Final[Path] = self._get_project_root()

            self.env_file_path: Path = self.PROJECT_ROOT / Path(".env")
            self.old_env_value: str | None = os.environ.get(self.env_variable_name)

        def __enter__(self) -> None:
            """Delete all stored instances of the stored environment variable."""
            if self.env_file_path.is_file():
                self.env_file_path = self.env_file_path.rename(
                    self.PROJECT_ROOT / Path(".env.original")
                )

            if self.old_env_value is not None:
                del os.environ[self.env_variable_name]

        def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType) -> None:  # noqa: E501
            """Restore the deleted environment variable to its previous states."""
            if self.env_file_path.is_file():
                self.env_file_path.rename(self.PROJECT_ROOT / Path(".env"))

            if self.old_env_value is not None:
                os.environ[self.env_variable_name] = self.old_env_value


class TestMain(BaseTestArgumentParser):
    """Test case to unit-test the main argument parser."""

    UTILITY_FUNCTIONS: frozenset[type[UtilityFunction]] = frozenset()

    @classmethod
    def test_error_when_no_function(cls, capsys: CaptureFixture[str]) -> None:
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
    def test_error_when_invalid_function(cls, capsys: CaptureFixture[str]) -> None:
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
    def test_attaching_utility_function(cls, capsys: CaptureFixture[str], help_argument: str) -> None:  # noqa: E501
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


class TestInviteURLGenerator(BaseTestArgumentParser):
    """
    Test case to unit-test the generate_invite_url utility function component.

    Includes tests for both the argument parser & low-level URL generation function.
    """

    UTILITY_FUNCTIONS: frozenset[type[UtilityFunction]] = frozenset({InviteURLGenerator})

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def USAGE_MESSAGE(cls) -> str:  # noqa: N805,N802
        """The error message describing how the given function should be called."""  # noqa: D401
        return (
            "usage: utils generate_invite_url [-h] "
            "discord_bot_application_id [discord_guild_id]"
        )

    @classmethod
    def execute_argument_parser_function(cls, args: Sequence[str], capsys: CaptureFixture[str], utility_functions: Iterable[type[UtilityFunction]] | None = None, *, delete_env_guild_id: bool = True) -> tuple[int, CaptureResult[str]]:  # noqa: E501
        """
        Execute the given utility function.

        The command line outputs are stored in class variables for later access.
        """
        env_guild_id_deleter: BaseTestArgumentParser.EmptyContextManager = (
            cls.EnvVariableDeleter(env_variable_name="GUILD_ID")
            if delete_env_guild_id
            else cls.EmptyContextManager()
        )

        with env_guild_id_deleter:
            return super().execute_argument_parser_function(args, capsys, utility_functions)

    @staticmethod
    def test_low_level_url_generates() -> None:
        """Test that the invite URL generates successfully when valid arguments are passed."""
        DISCORD_BOT_APPLICATION_ID: Final[str] = "".join(
            random.choices(string.digits, k=random.randint(17, 20))
        )
        DISCORD_GUILD_ID: Final[int] = random.randint(
            10000000000000000, 99999999999999999999
        )

        invite_url: str = InviteURLGenerator.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID, DISCORD_GUILD_ID
        )

        assert re.match(
            f"https://discord.com/.*={DISCORD_BOT_APPLICATION_ID}.*={DISCORD_GUILD_ID}",
            invite_url
        )

    @classmethod
    def test_parser_generates_url_with_discord_guild_id_as_environment_variable(cls, capsys: CaptureFixture[str]) -> None:  # noqa: E501
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

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            ["generate_invite_url", str(DISCORD_BOT_APPLICATION_ID)],
            capsys,
            delete_env_guild_id=False
        )

        if old_env_discord_guild_id:
            os.environ["DISCORD_GUILD_ID"] = old_env_discord_guild_id
        else:
            del os.environ["DISCORD_GUILD_ID"]

        assert return_code == 0
        assert not capture_result.err
        assert capture_result.out.strip() == InviteURLGenerator.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID,
            DISCORD_GUILD_ID
        )

    @classmethod
    def test_parser_generates_url_with_discord_guild_id_as_argument(cls, capsys: CaptureFixture[str]) -> None:  # noqa: E501
        """Test for the correct response when discord_guild_id is provided as an argument."""
        DISCORD_BOT_APPLICATION_ID: Final[str] = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        DISCORD_GUILD_ID: Final[int] = random.randint(
            10000000000000000,
            99999999999999999999
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            ["generate_invite_url", DISCORD_BOT_APPLICATION_ID, str(DISCORD_GUILD_ID)],
            capsys
        )

        assert return_code == 0
        assert not capture_result.err
        assert capture_result.out.strip() == InviteURLGenerator.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID,
            DISCORD_GUILD_ID
        )

    @classmethod
    def test_parser_error_when_no_discord_bot_application_id(cls, capsys: CaptureFixture[str]) -> None:  # noqa: E501
        """Test for the correct error when no discord_bot_application_id is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils generate_invite_url: error: the following arguments are required: "
            "discord_bot_application_id"
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            ["generate_invite_url"],
            capsys
        )

        assert return_code != 0
        assert not capture_result.out
        assert cls.USAGE_MESSAGE in " ".join(capture_result.err.replace("\n", "").split())
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    def test_parser_error_when_invalid_discord_bot_application_id(cls, capsys: CaptureFixture[str]) -> None:  # noqa: E501
        """Test for the correct error with an invalid discord_bot_application_id."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils generate_invite_url: error: discord_bot_application_id must be "
            "a valid Discord application ID "
            "(see https://support-dev.discord.com/hc/en-gb/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-)"
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            [
                "generate_invite_url",
                "".join(random.choices(string.ascii_letters + string.digits, k=7))
            ],
            capsys
        )

        assert return_code != 0
        assert not capture_result.out
        assert cls.USAGE_MESSAGE in " ".join(capture_result.err.replace("\n", "").split())
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    def test_parser_error_when_no_discord_guild_id(cls, capsys: CaptureFixture[str]) -> None:
        """Test for the correct error when no discord_guild_id is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils generate_invite_url: error: discord_guild_id must be provided as an "
            "argument to the generate_invite_url utility function or otherwise set "
            "the DISCORD_GUILD_ID environment variable"
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            [
                "generate_invite_url",
                "".join(random.choices(string.digits, k=random.randint(17, 20)))
            ],
            capsys,
            delete_env_guild_id=True
        )

        assert return_code != 0
        assert not capture_result.out
        assert cls.USAGE_MESSAGE in " ".join(capture_result.err.replace("\n", "").split())
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    def test_parser_error_when_invalid_discord_guild_id(cls, capsys: CaptureFixture[str]) -> None:  # noqa: E501
        """Test for the correct error when an invalid discord_guild_id is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils generate_invite_url: error: discord_guild_id must be "
            "a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            [
                "generate_invite_url",
                str(random.randint(10000000000000000, 99999999999999999999)),
                "".join(random.choices(string.ascii_letters + string.digits, k=7))
            ],
            capsys
        )

        assert return_code != 0
        assert not capture_result.out
        assert cls.USAGE_MESSAGE in " ".join(capture_result.err.replace("\n", "").split())
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    def test_parser_error_when_too_many_arguments(cls, capsys: CaptureFixture[str]) -> None:
        """Test for the correct error when too many arguments are provided."""
        EXTRA_ARGUMENT: Final[str] = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils: error: "
            f"unrecognized arguments: {EXTRA_ARGUMENT}"
        )

        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            [
                "generate_invite_url",
                str(random.randint(10000000000000000, 99999999999999999999)),
                str(random.randint(10000000000000000, 99999999999999999999)),
                EXTRA_ARGUMENT
            ],
            capsys
        )

        assert return_code != 0
        assert not capture_result.out
        assert super().USAGE_MESSAGE in capture_result.err
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    @pytest.mark.parametrize("help_argument", ("-h", "--help"))
    def test_parser_help(cls, capsys: CaptureFixture[str], help_argument: str) -> None:
        """Test for the correct response when any of the help arguments are provided."""
        return_code: int
        capture_result: CaptureResult[str]
        return_code, capture_result = cls.execute_argument_parser_function(
            ["generate_invite_url", help_argument],
            capsys
        )

        assert return_code == 0
        assert not capture_result.err
        assert cls.USAGE_MESSAGE in " ".join(capture_result.out.replace("\n", "").split())
        assert "positional arguments:" in capture_result.out
