"""
    Test suite for utils.py
"""

import os
import random
import re
import string
import subprocess
import sys

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from utils import generate_invite_url


class TestGenerateInviteURL:
    """ Test case to unit-test the low-level URL generation function. """

    @staticmethod
    def test_url_generates() -> None:
        """
            Test that the invite URL generates successfully when valid arguments
            are passed to the generation function.
        """

        discord_bot_application_id: str = "".join(
            random.choices(string.digits, k=random.randint(17, 20))
        )
        discord_guild_id: int = random.randint(
            10000000000000000,
            99999999999999999999
        )

        invite_url: str = generate_invite_url(
            discord_bot_application_id,
            discord_guild_id
        )

        assert re.match(
            f"https://discord.com/.*={discord_bot_application_id}.*={discord_guild_id}",
            invite_url
        )


class BaseTestArgumentParser:
    """
        Parent class to define the execution code used by all ArgumentParser
        test cases.
    """

    parser_output_return_code: int
    parser_output_stdout: str
    parser_output_stderr: str

    @classmethod
    def execute_util_function(cls, util_function_name: str, *arguments: str) -> None:
        """
            Common function to execute the given utility function and store the
            command line outputs in class variables.
        """

        if not re.match(r"\A[a-zA-Z0-9._\-+!\"' ]*\Z", util_function_name):  # NOTE: Because executing utils.py from a command-line subprocess requires it to be spawned as a shell, security issues can occur. Therefore loose validation checks are required for the values of util_function_name & arguments (see https://stackoverflow.com/a/29023432/14403974)
            raise TypeError(f"util_function_name must be a valid function name for the utils.py command-line program.")

        if any(not re.match(r"\A[a-zA-Z0-9._\-+!\"' ]*\Z", argument) for argument in arguments):
            raise ValueError("All arguments must be valid arguments for the utils.py command-line program.")

        project_root: Path = Path(__file__).resolve()
        for _ in range(6):
            project_root = project_root.parent

            if "README.md" in (path.name for path in Path(".").parent.iterdir()):
                break
        else:
            raise FileNotFoundError("Could not locate project root directory.")

        parser_output: CompletedProcess = subprocess.run(
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
    """ Test case to unit-test the overall argument parser. """

    @classmethod
    def test_error_when_no_function(cls) -> None:
        """
            Test that the correct error is displayed when no function name is
            provided.
        """

        cls.execute_util_function(util_function_name="")

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stderr
        assert "utils.py: error: the following arguments are required: function" in cls.parser_output_stderr

    @classmethod
    def test_error_when_invalid_function(cls) -> None:
        """
            Test that the correct error is displayed when an invalid function
            name is provided.
        """

        invalid_function: str = "".join(
            random.choices(string.ascii_letters + string.digits, k=7)
        )
        cls.execute_util_function(util_function_name=invalid_function)

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stderr
        assert f"utils.py: error: argument function: invalid choice: '{invalid_function}' (choose from 'generate_invite_url')" in cls.parser_output_stderr

    @classmethod
    @pytest.mark.parametrize("help_argument", ["-h", "--help"])
    def test_help(cls, help_argument: str) -> None:
        """
            Test that the correct response is given when any of the help
            arguments are provided.
        """

        cls.execute_util_function("", help_argument)

        assert cls.parser_output_return_code == 0
        assert not cls.parser_output_stderr
        assert "usage: utils.py [-h] {generate_invite_url}" in cls.parser_output_stdout
        assert "functions:" in cls.parser_output_stdout


class TestGenerateInviteURLArgumentParser(BaseTestArgumentParser):
    """ Test case to unit-test the generate_invite_url argument parser. """

    @classmethod
    def execute_util_function(cls, util_function_name: str, *arguments: str) -> None:
        """
            Common function to execute the given utility function and store the
            command line outputs in class variables.
        """

        env_file_path: Path = Path(".env")
        if env_file_path.is_file():
            env_file_path = env_file_path.rename(Path("temp.env"))

        super().execute_util_function(util_function_name, *arguments)

        if env_file_path.is_file():
            env_file_path.rename(Path(".env"))

    @classmethod
    def test_url_generates_without_discord_guild_id_environment_variable(cls) -> None:
        """
            Test that the correct response is given when the discord_guild_id is
            provided as an environment variable.
        """

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
            discord_bot_application_id
        )

        if old_env_discord_guild_id:
            os.environ["DISCORD_GUILD_ID"] = old_env_discord_guild_id
        else:
            del os.environ["DISCORD_GUILD_ID"]

        assert cls.parser_output_return_code == 0
        assert not cls.parser_output_stderr
        assert cls.parser_output_stdout == generate_invite_url(
            discord_bot_application_id,
            discord_guild_id
        )

    @classmethod
    def test_url_generates_with_discord_guild_id_environment_variable(cls) -> None:
        """
            Test that the correct response is given when the discord_guild_id is
            provided as a function argument.
        """

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
        assert cls.parser_output_stdout == generate_invite_url(
            discord_bot_application_id,
            discord_guild_id
        )

    @classmethod
    def test_error_when_no_discord_bot_application_id(cls) -> None:
        """
            Test that the correct error is displayed when no
            discord_bot_application_id is provided.
        """

        cls.execute_util_function(util_function_name="generate_invite_url")

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py generate_invite_url [-h] discord_bot_application_id [discord_guild_id]" in cls.parser_output_stderr
        assert "utils.py generate_invite_url: error: the following arguments are required: discord_bot_application_id" in cls.parser_output_stderr

    @classmethod
    def test_error_when_invalid_discord_bot_application_id(cls) -> None:
        """
            Test that the correct error is displayed when an invalid
            discord_bot_application_id is provided.
        """

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
        """
            Test that the correct error is displayed when no discord_guild_id is
            provided.
        """

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
        """
            Test that the correct error is displayed when an invalid
            discord_guild_id is provided.
        """

        invalid_discord_guild_id: str = "".join(
            random.choices(string.ascii_letters + string.digits, k=7)
        )
        cls.execute_util_function(
            "generate_invite_url",
            str(
                random.randint(10000000000000000, 99999999999999999999)
            ),
            invalid_discord_guild_id
        )

        assert cls.parser_output_return_code != 0
        assert not cls.parser_output_stdout
        assert "usage: utils.py generate_invite_url [-h] discord_bot_application_id [discord_guild_id]" in cls.parser_output_stderr
        assert "utils.py generate_invite_url: error: discord_guild_id must be a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)" in cls.parser_output_stderr

    @classmethod
    def test_error_when_too_many_arguments(cls) -> None:
        """
            Test that the correct error is displayed when too many arguments are
            provided.
        """

        extra_argument: str = str(
            random.randint(10000000000000000, 99999999999999999999)
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
        assert f"utils.py: error: unrecognized arguments: {extra_argument}" in cls.parser_output_stderr
