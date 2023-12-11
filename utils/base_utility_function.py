"""Base component definition of a generic Utility Function."""

import abc
import logging
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
