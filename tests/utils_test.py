"""Test suite for utils.py."""

import os
import random
import re
import string
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess

import discord
import pytest

import utils


class TestGenerateInviteURL:
    """Test case to unit-test the low-level URL generation function."""

    @staticmethod
    def test_url_generates() -> None:
        """Test that the invite URL generates successfully when valid arguments are passed."""
        discord_bot_application_id: str = "".join(
            random.choices(string.digits, k=random.randint(17, 20))
        )
        discord_guild_id: int = random.randint(
            10000000000000000,
            99999999999999999999
        )

        invite_url: str = utils.generate_invite_url(
            discord_bot_application_id,
            discord_guild_id
        )

        assert re.match(
            f"https://discord.com/.*={discord_bot_application_id}.*={discord_guild_id}",
            invite_url
        )


class TestPlotBarChart:
    """Test case to unit-test the plot_bar_chart function."""

    def test_bar_chart_generates(self) -> None:
        """Test that the bar chart generates successfully when valid arguments are passed."""
        filename: str = "output_chart.png"
        description: str = "Bar chart of the counted value of different roles."

        bar_chart_image: discord.File = utils.plot_bar_chart(
            data={"role1": 5, "role2": 7},
            xlabel="Role Name",
            ylabel="Counted value",
            title="Counted Value Of Each Role",
            filename=filename,
            description=description,
            extra_text="This is extra text"
        )

        assert bar_chart_image.filename == filename
        assert bar_chart_image.description == description
        assert bool(bar_chart_image.fp.read()) is True


class TestAmountOfTimeFormatter:
    """Test case to unit-test the amount_of_time_formatter function."""

    @pytest.mark.parametrize(
        "time_value",
        (1, 1.0, 0.999999, 1.000001)
    )
    def test_format_unit_value(self, time_value: float) -> None:
        """Test that a value of one only includes the time_scale."""
        time_scale: str = "day"

        formatted_amount_of_time: str = utils.amount_of_time_formatter(time_value, time_scale)

        assert formatted_amount_of_time == time_scale
        assert not formatted_amount_of_time.endswith("s")

    # noinspection PyTypeChecker
    @pytest.mark.parametrize(
        "time_value",
        tuple(range(2, 21)) + (2.00, 0, 0.0, 25.0, -0, -0.0, -25.0)
    )
    def test_format_integer_value(self, time_value: float) -> None:
        """Test that an integer value includes the value and time_scale pluralized."""
        time_scale: str = "day"

        assert utils.amount_of_time_formatter(
            time_value,
            time_scale
        ) == f"{int(time_value)} {time_scale}s"

    @pytest.mark.parametrize("time_value", (3.14159, 0.005, 25.0333333))
    def test_format_float_value(self, time_value: float) -> None:
        """Test that a float value includes the rounded value and time_scale pluralized."""
        time_scale: str = "day"

        assert utils.amount_of_time_formatter(
            time_value,
            time_scale
        ) == f"{time_value:.2f} {time_scale}s"


class BaseTestArgumentParser:
    """Parent class to define the execution code used by all ArgumentParser test cases."""

    parser_output_return_code: int
    parser_output_stdout: str
    parser_output_stderr: str

    @classmethod
    def execute_util_function(cls, util_function_name: str, *arguments: str) -> None:
        """
        Execute the given utility function.

        The command line outputs are stored in class variables for later access.
        """
        if not re.match(r"\A[a-zA-Z0-9._\-+!\"' ]*\Z", util_function_name):  # NOTE: Because executing utils.py from a command-line subprocess requires it to be spawned as a shell, security issues can occur. Therefore loose validation checks are required for the values of util_function_name & arguments (see https://stackoverflow.com/a/29023432/14403974)
            raise TypeError("util_function_name must be a valid function name for the utils.py command-line program.")

        if any(not re.match(r"\A[a-zA-Z0-9._\-+!\"' ]*\Z", argument) for argument in arguments):
            raise ValueError("All arguments must be valid arguments for the utils.py command-line program.")

        project_root: Path = Path(__file__).resolve()
        for _ in range(6):
            project_root = project_root.parent

            if "README.md" in (path.name for path in Path(".").parent.iterdir()):
                break
        else:
            raise FileNotFoundError("Could not locate project root directory.")

        parser_output: CompletedProcess[bytes] = subprocess.run(
            f"""{sys.executable} utils.py{" " if util_function_name else ""}{util_function_name}{" " if arguments else ""}{" ".join(arguments)}""",
            shell=True,
            cwd=project_root.parent,
            capture_output=True
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
        cls.execute_util_function(util_function_name="")

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stderr
        assert "utils.py: error: the following arguments are required: function" in cls.parser_output_stderr

    @classmethod
    def test_error_when_invalid_function(cls) -> None:
        """Test for the correct error when an invalid function name is provided."""
        invalid_function: str = "".join(
            random.choices(string.ascii_letters + string.digits, k=7)
        )
        cls.execute_util_function(util_function_name=invalid_function)

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stderr
        assert f"utils.py: error: argument function: invalid choice: '{invalid_function}' (choose from 'generate_invite_url')" in cls.parser_output_stderr

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
    def execute_util_function(cls, util_function_name: str, *arguments: str, delete_env_guild_id: bool = True) -> None:
        """
        Execute the given utility function.

        The command line outputs are stored in class variables for later access.
        """
        env_file_path: Path = Path(".env")
        if env_file_path.is_file():
            env_file_path = env_file_path.rename(Path("temp.env"))

        old_env_discord_guild_id: str | None = os.environ.get("DISCORD_GUILD_ID")
        if delete_env_guild_id and old_env_discord_guild_id is not None:
            del os.environ["DISCORD_GUILD_ID"]

        super().execute_util_function(util_function_name, *arguments)

        if delete_env_guild_id and old_env_discord_guild_id is not None:
            os.environ["DISCORD_GUILD_ID"] = old_env_discord_guild_id

        if env_file_path.is_file():
            env_file_path.rename(Path(".env"))

    @classmethod
    def test_url_generates_without_discord_guild_id_environment_variable(cls) -> None:
        """Test for the correct response when discord_guild_id is given as an env variable."""
        discord_bot_application_id: str = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        discord_guild_id: int = random.randint(
            10000000000000000,
            99999999999999999999
        )

        old_env_discord_guild_id: str = os.environ.get("DISCORD_GUILD_ID", "")
        os.environ["DISCORD_GUILD_ID"] = str(discord_guild_id)

        cls.execute_util_function(
            "generate_invite_url",
            discord_bot_application_id,
            delete_env_guild_id=False
        )

        if old_env_discord_guild_id:
            os.environ["DISCORD_GUILD_ID"] = old_env_discord_guild_id
        else:
            del os.environ["DISCORD_GUILD_ID"]

        assert cls.parser_output_return_code == 0
        assert not cls.parser_output_stderr
        assert cls.parser_output_stdout == utils.generate_invite_url(
            discord_bot_application_id,
            discord_guild_id
        )

    @classmethod
    def test_url_generates_with_discord_guild_id_environment_variable(cls) -> None:
        """Test for the correct response when discord_guild_id is provided as an argument."""
        discord_bot_application_id: str = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        discord_guild_id: int = random.randint(
            10000000000000000,
            99999999999999999999
        )

        cls.execute_util_function(
            "generate_invite_url",
            discord_bot_application_id,
            str(discord_guild_id)
        )

        assert cls.parser_output_return_code == 0
        assert not cls.parser_output_stderr
        assert cls.parser_output_stdout == utils.generate_invite_url(
            discord_bot_application_id,
            discord_guild_id
        )

    @classmethod
    def test_error_when_no_discord_bot_application_id(cls) -> None:
        """Test for the correct error when no discord_bot_application_id is provided."""
        cls.execute_util_function(util_function_name="generate_invite_url")

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py generate_invite_url [-h] discord_bot_application_id [discord_guild_id]" in cls.parser_output_stderr
        assert "utils.py generate_invite_url: error: the following arguments are required: discord_bot_application_id" in cls.parser_output_stderr

    @classmethod
    def test_error_when_invalid_discord_bot_application_id(cls) -> None:
        """Test for the correct error with an invalid discord_bot_application_id."""
        invalid_discord_bot_application_id: str = "".join(
            random.choices(string.ascii_letters + string.digits, k=7)
        )
        cls.execute_util_function(
            "generate_invite_url",
            invalid_discord_bot_application_id
        )

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py generate_invite_url [-h] discord_bot_application_id [discord_guild_id]" in cls.parser_output_stderr
        assert ("utils.py generate_invite_url: error: discord_bot_application_id must be a valid Discord application ID (see https://support-dev.discord.com/hc/en-gb/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-)" in cls.parser_output_stderr)

    @classmethod
    def test_error_when_no_discord_guild_id(cls) -> None:
        """Test for the correct error when no discord_guild_id is provided."""
        cls.execute_util_function(
            "generate_invite_url",
            "".join(
                random.choices(string.digits, k=random.randint(17, 20))
            )
        )

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py generate_invite_url [-h] discord_bot_application_id [discord_guild_id]" in cls.parser_output_stderr
        assert "utils.py generate_invite_url: error: discord_guild_id must be provided as an argument to the generate_invite_url utility function or otherwise set the DISCORD_GUILD_ID environment variable" in cls.parser_output_stderr

    @classmethod
    def test_error_when_invalid_discord_guild_id(cls) -> None:
        """Test for the correct error when an invalid discord_guild_id is provided."""
        expected_usage_message: str = (
            "usage: utils.py generate_invite_url [-h]"
            " discord_bot_application_id [discord_guild_id]"
        )
        expected_error_message: str = (
            "utils.py generate_invite_url: error: discord_guild_id must be"
            " a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
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
        assert expected_usage_message in cls.parser_output_stderr
        assert expected_error_message in cls.parser_output_stderr

    @classmethod
    def test_error_when_too_many_arguments(cls) -> None:
        """Test for the correct error when too many arguments are provided."""
        extra_argument: str = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        expected_error_message: str = (
            "utils.py: error:"
            f" unrecognized arguments: {extra_argument}"
        )

        cls.execute_util_function(
            "generate_invite_url",
            str(
                random.randint(10000000000000000, 99999999999999999999)
            ),
            str(
                random.randint(10000000000000000, 99999999999999999999)
            ),
            extra_argument
        )

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stderr
        assert expected_error_message in cls.parser_output_stderr
