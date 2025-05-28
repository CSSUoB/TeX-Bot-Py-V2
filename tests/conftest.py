"""Execute additional logic before/after tests are collected."""

import os
import random
import string
from pathlib import Path
from typing import TYPE_CHECKING

import dotenv

import config

from .test_utils import RandomDiscordBotTokenGenerator, RandomDiscordGuildIDGenerator

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from typing import Final, Literal, TextIO

    import pytest

_EXISTING_ENV_VARIABLES: "Final[Mapping[str, object]]" = {
    **dotenv.dotenv_values(),
    **os.environ,
}
MISSING_ENV_VARIABLES: "Final[Mapping[str, object]]" = {
    key: value
    for key, value in (
        {
            "DISCORD_BOT_TOKEN": RandomDiscordBotTokenGenerator.single_value(),
            "DISCORD_GUILD_ID": RandomDiscordGuildIDGenerator.single_value(),
            "MODERATION_DOCUMENT_URL": "https://google.com",
            "MEMBERS_LIST_URL": "https://google.com",
            "MEMBERS_LIST_URL_SESSION_COOKIE": (
                "".join(random.choices(string.hexdigits, k=random.randint(128, 256)))  # noqa: S311
            ),
        }.items()
    )
    if key not in _EXISTING_ENV_VARIABLES
}

dotenv_file_path: Path | None = None
dotenv_file_open_method: "Literal['a', 'w']" = "a"

if MISSING_ENV_VARIABLES:
    RAW_DOTENV_FILE_PATH: "Final[str]" = dotenv.find_dotenv()
    if not RAW_DOTENV_FILE_PATH:
        dotenv_file_path = config.PROJECT_ROOT / ".env"
        dotenv_file_open_method = "w"
    else:
        dotenv_file_path = Path(RAW_DOTENV_FILE_PATH)


def pytest_sessionstart(session: "pytest.Session") -> None:  # noqa: ARG001
    """
    Called after the Session object has been created and before performing collection and entering the run test loop.

    Tasks run upon session finishing:
        * Add any additional required environment variables that have not been set,
            but are needed before running any tests
    """  # noqa: D401,W505,E501
    if MISSING_ENV_VARIABLES and dotenv_file_path is not None:
        with dotenv_file_path.open(dotenv_file_open_method) as dotenv_file:
            dotenv_file.write(
                "\n".join(f"{key}={value}" for key, value in MISSING_ENV_VARIABLES.items()),
            )
            dotenv_file.write("\n")


# noinspection SpellCheckingInspection,PyUnusedLocal
def pytest_sessionfinish(
    session: "pytest.Session", exitstatus: "int | pytest.ExitCode"
) -> None:
    """
    Called after whole test run finished, right before returning the exit status to the system.

    Tasks run upon session finishing:
        * Restoring any changed environment variables within the identified `.env` file
    """  # noqa: D401
    if MISSING_ENV_VARIABLES and dotenv_file_path is not None and dotenv_file_path.is_file():
        if dotenv_file_open_method == "w":
            dotenv_file_path.unlink()

        elif dotenv_file_open_method == "a":
            dotenv_file: TextIO
            with dotenv_file_path.open("r") as dotenv_file:
                ENV_VARIABLES: Final[Iterable[str]] = dotenv_file.readlines()

            with dotenv_file_path.open("w") as dotenv_file:
                dotenv_file.write(
                    "\n".join(
                        [
                            env_variable.strip()
                            for env_variable in ENV_VARIABLES
                            if (
                                env_variable.strip()
                                and (
                                    env_variable.strip().split("=", maxsplit=1)[0]
                                    not in MISSING_ENV_VARIABLES
                                )
                            )
                        ],
                    ),
                )
                dotenv_file.write("\n")
