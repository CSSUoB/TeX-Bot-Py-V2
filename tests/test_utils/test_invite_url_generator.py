import os
import random
import re
import string
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Final

import pytest
from classproperties import classproperty

from test_utils._testing_utils import BaseTestArgumentParser
from utils import InviteURLGenerator, UtilityFunction

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture, CaptureResult
    # noinspection PyProtectedMember
    from argparse import _SubParserAction as SubParserAction  # type: ignore[attr-defined]


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
    def execute_argument_parser_function(cls, args: Sequence[str], capsys: "CaptureFixture[str]", utility_functions: Iterable[type[UtilityFunction]] | None = None, *, delete_env_guild_id: bool = True) -> tuple[int, "CaptureResult[str]"]:  # noqa: E501
        """
        Execute the given utility function.

        The command line outputs are stored in class variables for later access.
        """
        env_guild_id_deleter: BaseTestArgumentParser.EmptyContextManager = (
            cls.EnvVariableDeleter(env_variable_name="DISCORD_GUILD_ID")
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
    def test_parser_generates_url_with_discord_guild_id_as_environment_variable(cls, capsys: "CaptureFixture[str]") -> None:  # noqa: E501
        """Test for the correct response when discord_guild_id is given as an env variable."""
        DISCORD_BOT_APPLICATION_ID: Final[str] = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        DISCORD_GUILD_ID: Final[int] = random.randint(
            10000000000000000,
            99999999999999999999
        )

        old_env_discord_guild_id: str | None = os.environ.get("DISCORD_GUILD_ID")
        os.environ["DISCORD_GUILD_ID"] = str(DISCORD_GUILD_ID)

        RETURN_CODE: int
        CAPTURE_RESULT: "CaptureResult[str]"
        RETURN_CODE, CAPTURE_RESULT = cls.execute_argument_parser_function(
            ["generate_invite_url", str(DISCORD_BOT_APPLICATION_ID)],
            capsys,
            delete_env_guild_id=False
        )

        if old_env_discord_guild_id:
            os.environ["DISCORD_GUILD_ID"] = old_env_discord_guild_id
        else:
            del os.environ["DISCORD_GUILD_ID"]

        assert RETURN_CODE == 0
        assert not CAPTURE_RESULT.err
        assert CAPTURE_RESULT.out.strip() == InviteURLGenerator.generate_invite_url(
            DISCORD_BOT_APPLICATION_ID,
            DISCORD_GUILD_ID
        )

    @classmethod
    def test_parser_generates_url_with_discord_guild_id_as_argument(cls, capsys: "CaptureFixture[str]") -> None:  # noqa: E501
        """Test for the correct response when discord_guild_id is provided as an argument."""
        DISCORD_BOT_APPLICATION_ID: Final[str] = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        DISCORD_GUILD_ID: Final[int] = random.randint(
            10000000000000000,
            99999999999999999999
        )

        return_code: int
        capture_result: "CaptureResult[str]"
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
    def test_parser_error_when_no_discord_bot_application_id(cls, capsys: "CaptureFixture[str]") -> None:  # noqa: E501
        """Test for the correct error when no discord_bot_application_id is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils generate_invite_url: error: the following arguments are required: "
            "discord_bot_application_id"
        )

        return_code: int
        capture_result: "CaptureResult[str]"
        return_code, capture_result = cls.execute_argument_parser_function(
            ["generate_invite_url"],
            capsys
        )

        assert return_code != 0
        assert not capture_result.out
        assert cls.USAGE_MESSAGE in " ".join(capture_result.err.replace("\n", "").split())
        assert EXPECTED_ERROR_MESSAGE in capture_result.err

    @classmethod
    def test_parser_error_when_invalid_discord_bot_application_id(cls, capsys: "CaptureFixture[str]") -> None:  # noqa: E501
        """Test for the correct error with an invalid discord_bot_application_id."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils generate_invite_url: error: discord_bot_application_id must be "
            "a valid Discord application ID "
            "(see https://support-dev.discord.com/hc/en-gb/articles/360028717192-Where-can-I-find-my-Application-Team-Server-ID-)"
        )

        return_code: int
        capture_result: "CaptureResult[str]"
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
    def test_parser_error_when_no_discord_guild_id(cls, capsys: "CaptureFixture[str]") -> None:
        """Test for the correct error when no discord_guild_id is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils generate_invite_url: error: discord_guild_id must be provided as an "
            "argument to the generate_invite_url utility function or otherwise set "
            "the DISCORD_GUILD_ID environment variable"
        )

        return_code: int
        capture_result: "CaptureResult[str]"
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
    def test_parser_error_when_invalid_discord_guild_id(cls, capsys: "CaptureFixture[str]") -> None:  # noqa: E501
        """Test for the correct error when an invalid discord_guild_id is provided."""
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils generate_invite_url: error: discord_guild_id must be "
            "a valid Discord guild ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)"
        )

        return_code: int
        capture_result: "CaptureResult[str]"
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
    def test_parser_error_when_too_many_arguments(cls, capsys: "CaptureFixture[str]") -> None:
        """Test for the correct error when too many arguments are provided."""
        EXTRA_ARGUMENT: Final[str] = str(
            random.randint(10000000000000000, 99999999999999999999)
        )
        EXPECTED_ERROR_MESSAGE: Final[str] = (
            "utils: error: "
            f"unrecognized arguments: {EXTRA_ARGUMENT}"
        )

        return_code: int
        capture_result: "CaptureResult[str]"
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
    def test_parser_help(cls, capsys: "CaptureFixture[str]", help_argument: str) -> None:
        """Test for the correct response when any of the help arguments are provided."""
        return_code: int
        capture_result: "CaptureResult[str]"
        return_code, capture_result = cls.execute_argument_parser_function(
            ["generate_invite_url", help_argument],
            capsys
        )

        assert return_code == 0
        assert not capture_result.err
        assert cls.USAGE_MESSAGE in " ".join(capture_result.out.replace("\n", "").split())
        assert "positional arguments:" in capture_result.out
