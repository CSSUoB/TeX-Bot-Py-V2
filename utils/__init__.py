"""Utility classes & functions provided for use across the whole of the project."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "CommandChecks",
    "InviteURLGenerator",
    "main",
    "MessageSenderComponent",
    "SuppressTraceback",
    "TeXBot",
    "TeXBotBaseCog",
    "TeXBotApplicationContext",
    "TeXBotAutocompleteContext",
    "UtilityFunction",
)

from argparse import ArgumentParser, Namespace
from collections.abc import Iterable
from typing import TYPE_CHECKING, Final

from utils.base_utility_function import UtilityFunction
from utils.command_checks import CommandChecks
from utils.generate_invite_url import InviteURLGenerator
from utils.message_sender_components import MessageSenderComponent
from utils.suppress_traceback import SuppressTraceback
from utils.tex_bot import TeXBot
from utils.tex_bot_base_cog import TeXBotBaseCog
from utils.tex_bot_contexts import TeXBotApplicationContext, TeXBotAutocompleteContext

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from argparse import _SubParsersAction as SubParsersAction


def main(argv: Sequence[str] | None = None, utility_functions: Iterable[type[UtilityFunction]] | None = None) -> int:  # noqa: E501
    """Run this script as a CLI tool with argument parsing."""
    utility_functions = set() if utility_functions is None else set(utility_functions)

    arg_parser: ArgumentParser = ArgumentParser(
        prog="utils",
        description="Executes common command-line utility functions"
    )
    function_subparsers: SubParsersAction[ArgumentParser] = arg_parser.add_subparsers(
        title="functions",
        required=True,
        help="Utility function to execute",
        dest="function"
    )

    utility_function: type[UtilityFunction]
    for utility_function in utility_functions:
        utility_function.attach_to_parser(function_subparsers)

    parsed_args: Namespace = arg_parser.parse_args(argv)

    for utility_function in utility_functions:
        if parsed_args.function == utility_function.NAME:
            return utility_function.run(parsed_args, function_subparsers)

    NO_FUNCTION_EXECUTED_MESSAGE: Final[str] = (
        "Valid function name provided, but not executed."
    )
    raise RuntimeError(NO_FUNCTION_EXECUTED_MESSAGE)
