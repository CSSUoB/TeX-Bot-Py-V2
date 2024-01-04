"""Base component definition of a generic Utility Function."""

from collections.abc import Sequence

__all__: Sequence[str] = ("UtilityFunction",)

import abc
import logging
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING, ClassVar, Final, Self

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from argparse import _SubParsersAction as SubParsersAction


class UtilityFunction(abc.ABC):
    """
    Abstract component of a utility function.

    Subclasses declare the actual execution logic of each utility function.
    """

    NAME: str
    DESCRIPTION: str
    _function_subparsers: ClassVar[dict["SubParsersAction[ArgumentParser]", ArgumentParser]] = {}  # noqa: E501

    # noinspection PyTypeChecker,PyTypeHints
    def __new__(cls, *_args: object, **_kwargs: object) -> Self:
        """Instance objects of UtilityFunctions cannot be instantiated."""
        CANNOT_INSTANTIATE_INSTANCE_MESSAGE: Final[str] = (
            f"Cannot instantiate {cls.__name__} object instance."
        )
        raise RuntimeError(CANNOT_INSTANTIATE_INSTANCE_MESSAGE)

    @classmethod
    def attach_to_parser(cls, parser: "SubParsersAction[ArgumentParser]") -> None:
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
    def run(cls, parsed_args: Namespace, parser: "SubParsersAction[ArgumentParser]") -> int:
        """Execute the logic that this util function provides."""
