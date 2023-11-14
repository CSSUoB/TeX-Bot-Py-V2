"""Test suite for utils.py."""

import os
import random
import re
import string
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess
from typing import TYPE_CHECKING, Final

import pytest

import utils

if TYPE_CHECKING:
    import discord


class TestGenerateInviteURL:
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

        invite_url: str = utils.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID,
            DISCORD_GUILD_ID
        )

        assert re.match(
            f"https://discord.com/.*={DISCORD_BOT_APPLICATION_ID}.*={DISCORD_GUILD_ID}",
            invite_url
        )


class TestPlotBarChart:
    """Test case to unit-test the plot_bar_chart function."""

    def test_bar_chart_generates(self) -> None:
        """Test that the bar chart generates successfully when valid arguments are passed."""
        FILENAME: Final[str] = "output_chart.png"
        DESCRIPTION: Final[str] = "Bar chart of the counted value of different roles."

        bar_chart_image: discord.File = utils.plot_bar_chart(
            data={"role1": 5, "role2": 7},
            xlabel="Role Name",
            ylabel="Counted value",
            title="Counted Value Of Each Role",
            filename=FILENAME,
            description=DESCRIPTION,
            extra_text="This is extra text"
        )

        assert bar_chart_image.filename == FILENAME
        assert bar_chart_image.description == DESCRIPTION
        assert bool(bar_chart_image.fp.read()) is True


class TestAmountOfTimeFormatter:
    """Test case to unit-test the amount_of_time_formatter function."""

    @pytest.mark.parametrize(
        "time_value",
        (1, 1.0, 0.999999, 1.000001)
    )
    def test_format_unit_value(self, time_value: float) -> None:
        """Test that a value of one only includes the time_scale."""
        TIME_SCALE: Final[str] = "day"

        formatted_amount_of_time: str = utils.amount_of_time_formatter(time_value, TIME_SCALE)

        assert formatted_amount_of_time == TIME_SCALE
        assert not formatted_amount_of_time.endswith("s")

    # noinspection PyTypeChecker
    @pytest.mark.parametrize(
        "time_value",
        (*range(2, 21), 2.00, 0, 0.0, 25.0, -0, -0.0, -25.0)
    )
    def test_format_integer_value(self, time_value: float) -> None:
        """Test that an integer value includes the value and time_scale pluralized."""
        TIME_SCALE: Final[str] = "day"

        assert utils.amount_of_time_formatter(
            time_value,
            TIME_SCALE
        ) == f"{int(time_value)} {TIME_SCALE}s"

    @pytest.mark.parametrize("time_value", (3.14159, 0.005, 25.0333333))
    def test_format_float_value(self, time_value: float) -> None:
        """Test that a float value includes the rounded value and time_scale pluralized."""
        TIME_SCALE: Final[str] = "day"

        assert utils.amount_of_time_formatter(
            time_value,
            TIME_SCALE
        ) == f"{time_value:.2f} {TIME_SCALE}s"


class BaseTestArgumentParser:
    """Parent class to define the execution code used by all ArgumentParser test cases."""

    parser_output_return_code: int
    parser_output_stdout: str
    parser_output_stderr: str

    @staticmethod
    def _get_project_root() -> Path:
        project_root: Path = Path(__file__).resolve()
        for _ in range(6):
            project_root = project_root.parent

            if "README.md" in (path.name for path in project_root.iterdir()):
                break
        else:
            # noinspection PyFinal
            NO_ROOT_DIRECTORY_MESSAGE: Final[str] = "Could not locate project root directory."
            raise FileNotFoundError(NO_ROOT_DIRECTORY_MESSAGE)

        return project_root

    @classmethod
    def execute_util_function(cls, util_function_name: str, *arguments: str) -> None:
        """
        Execute the given utility function.

        The command line outputs are stored in class variables for later access.
        """
        if not re.match(r"\A[a-zA-Z0-9._\-+!\"' ]*\Z", util_function_name):
            INVALID_FUNCTION_NAME_MESSAGE: Final[str] = (
                "util_function_name must be a valid function name for "
                "the utils.py command-line program."
            )
            raise TypeError(INVALID_FUNCTION_NAME_MESSAGE)

        arguments_contain_invalid_symbol: bool = any(
            not re.match(r"\A[a-zA-Z0-9._\-+!\"' ]*\Z", argument)
            for argument
            in arguments
        )
        if arguments_contain_invalid_symbol:
            INVALID_ARGUMENTS_MESSAGE: Final[str] = (
                "All arguments must be valid arguments for the utils.py command-line program."
            )
            raise ValueError(INVALID_ARGUMENTS_MESSAGE)

        subprocess_args: list[str] = [sys.executable, "-m", "utils"]
        if util_function_name:
            subprocess_args.append(util_function_name)
        subprocess_args.extend(arguments)

        parser_output: CompletedProcess[bytes] = subprocess.run(
            subprocess_args,  # noqa: S603
            cwd=cls._get_project_root(),
            capture_output=True,
            check=False
        )

        cls.parser_output_return_code = parser_output.returncode
        cls.parser_output_stdout = " ".join(
            parser_output.stdout.decode("utf-8").replace("\r\n", "").split()
        )
        cls.parser_output_stderr = " ".join(
            parser_output.stderr.decode("utf-8").replace("\r\n", "").split()
        )


class TestArgumentParser(BaseTestArgumentParser):
    """Test case to unit-test the overall argument parser."""

    @classmethod
    def test_error_when_no_function(cls) -> None:
        """Test for the correct error when no function name is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils.py: error: the following arguments are required: function"
        )

        cls.execute_util_function(util_function_name="")

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stderr
        assert EXPECTED_ERROR_MESSAGE in cls.parser_output_stderr

    @classmethod
    def test_error_when_invalid_function(cls) -> None:
        """Test for the correct error when an invalid function name is provided."""
        INVALID_FUNCTION: Final[str] = "".join(
            random.choices(string.ascii_letters + string.digits, k=7)
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils.py: error: argument function: invalid choice: "
            f"'{INVALID_FUNCTION}' (choose from 'generate_invite_url')"
        )

        cls.execute_util_function(util_function_name=INVALID_FUNCTION)

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stderr
        assert EXPECTED_ERROR_MESSAGE in cls.parser_output_stderr

    @classmethod
    @pytest.mark.parametrize("help_argument", ("-h", "--help"))
    def test_help(cls, help_argument: str) -> None:
        """Test for the correct response when any of the help arguments are provided."""
        cls.execute_util_function("", help_argument)

        assert cls.parser_output_return_code == 0
        assert not cls.parser_output_stderr
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stdout
        assert "functions:" in cls.parser_output_stdout


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
        assert cls.parser_output_stdout == utils.generate_invite_url(
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
        assert cls.parser_output_stdout == utils.generate_invite_url(
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
