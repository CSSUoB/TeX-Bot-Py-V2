"""Base component definition of a generic Utility Function."""

import abc
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from argparse import _SubParserAction as SubParserAction


class UtilityFunction(abc.ABC):
    """
    Abstract component of a utility function.

    Subclasses declare the actual execution logic of each utility function.
    """

    NAME: str
    DESCRIPTION: str

    def __init__(self) -> None:
        """Initialise the function_subparser attribute to None."""
        self.function_subparser: ArgumentParser | None = None

    def attach_to_parser(self, parser: SubParserAction) -> None:
        """
        Add a subparser to the provided argument parser.

        This allows the subparser to retrieve arguments specific to this utility function.
        """
        self.function_subparser = parser.add_parser(self.NAME, description=self.DESCRIPTION)

    @abc.abstractmethod
    def run(self, parsed_args: Namespace) -> int:
        """Execute the logic that this util function provides."""
        raise NotImplementedError
