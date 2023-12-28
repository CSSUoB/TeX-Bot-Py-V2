import abc
from collections.abc import Iterable, Sequence
from types import TracebackType
from typing import TYPE_CHECKING

from classproperties import classproperty

import utils
from utils import UtilityFunction

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture, CaptureResult


class EmptyContextManager:
    """Empty context manager that executes no logic when entering/exiting."""

    def __enter__(self) -> None:
        """Enter the context manager and execute no additional logic."""

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:  # noqa: E501
        """Exit the context manager and execute no additional logic."""


class BaseTestArgumentParser(abc.ABC):
    """Parent class to define the execution code used by all ArgumentParser test cases."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def UTILITY_FUNCTIONS(cls) -> frozenset[type[UtilityFunction]]:  # noqa: N802,N805
        """The set of utility function components associated with this specific test case."""  # noqa: D401

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def USAGE_MESSAGE(cls) -> str:  # noqa: N805,N802
        """The error message describing how the given function should be called."""  # noqa: D401
        return cls._format_usage_message(
            utility_function.NAME for utility_function in cls.UTILITY_FUNCTIONS
        )

    @staticmethod
    def _format_usage_message(utility_function_names: Iterable[str]) -> str:
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
