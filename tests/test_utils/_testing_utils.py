import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Final

from classproperties import classproperty

import utils
from utils import UtilityFunction

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture, CaptureResult
    # noinspection PyProtectedMember
    from argparse import _SubParserAction as SubParserAction  # type: ignore[attr-defined]


class BaseTestArgumentParser:  # TODO: make ABC
    """Parent class to define the execution code used by all ArgumentParser test cases."""

    UTILITY_FUNCTIONS: frozenset[type[UtilityFunction]]  # TODO: Make abstract classproperty

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
    def execute_argument_parser_function(cls, args: Sequence[str], capsys: "CaptureFixture[str]", utility_functions: Iterable[type[UtilityFunction]] | None = None) -> tuple[int, "CaptureResult[str]"]:  # noqa: E501
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

        def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:  # noqa: E501
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
