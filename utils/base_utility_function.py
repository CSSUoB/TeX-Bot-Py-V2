"""Base component definition of a generic Utility Function."""

import abc
import logging
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from typing import Any, ClassVar, Protocol


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
    _function_subparsers: ClassVar[dict[SubParserAction, ArgumentParser]] = {}

    @classmethod
    def attach_to_parser(cls, parser: SubParserAction) -> None:
        """
        Add a subparser to the provided argument parser.

        This allows the subparser to retrieve arguments specific to this utility function.
        """
        if parser in cls._function_subparsers:
            logging.warning(
                "This UtilityFunction has already been attached to the given parser."
            )
        else:
            cls._function_subparsers[parser] = parser.add_parser(
                cls.NAME,
                description=cls.DESCRIPTION
            )

    @classmethod
    @abc.abstractmethod
    def run(cls, parsed_args: Namespace, parser: SubParserAction) -> int:
        """Execute the logic that this util function provides."""
        raise NotImplementedError
