"""Base component definition of a generic Utility Function."""

import abc
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from typing import Any, Protocol


class UtilityFunction(abc.ABC):
    """
    Abstract component of a utility function.

    Subclasses declare the actual execution logic of each utility function.
    """

    class SubParserAction(Protocol):
        """One possible action for a given subparser argument."""

        def add_parser(self,  # noqa: PLR0913
                       name: str,
                       *,
                       help: str | None = ...,  # noqa: A002
                       aliases: Sequence[str] = ...,
                       prog: str | None = ...,
                       usage: str | None = ...,
                       description: str | None = ...,
                       epilog: str | None = ...,
                       prefix_chars: str = ...,
                       fromfile_prefix_chars: str | None = ...,
                       argument_default: Any = ...,
                       conflict_handler: str = ...,
                       add_help: bool = ...,
                       allow_abbrev: bool = ...,
                       exit_on_error: bool = ...,
                       **kwargs: Any) -> ArgumentParser:
            """Create a new subparser from this SubParserAction."""
            raise NotImplementedError

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
