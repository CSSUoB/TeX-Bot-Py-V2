"""Utility classes & functions provided for use across the whole of the project."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "CommandChecks",
    "InviteURLGenerator",
    "MessageSenderComponent",
    "SuppressTraceback",
    "TeXBot",
    "TeXBotBaseCog",
    "TeXBotApplicationContext",
    "TeXBotAutocompleteContext",
    "UtilityFunction",
)

from argparse import ArgumentParser, Namespace

from utils.base_utility_function import UtilityFunction
from utils.generate_invite_url import InviteURLGenerator

# NOTE: Preventing loading modules that would cause errors if this file has been run from the command-line without pre-initialisation
if __name__ != "__main__":
    from utils.command_checks import CommandChecks
    from utils.message_sender_components import MessageSenderComponent
    from utils.suppress_traceback import SuppressTraceback
    from utils.tex_bot import TeXBot
    from utils.tex_bot_base_cog import TeXBotBaseCog
    from utils.tex_bot_contexts import TeXBotApplicationContext, TeXBotAutocompleteContext


if __name__ == "__main__":
    arg_parser: ArgumentParser = ArgumentParser(
        description="Executes common command-line utility functions"
    )
    function_subparsers: UtilityFunction.SubParserAction = arg_parser.add_subparsers(  # type: ignore[assignment]
        title="functions",
        required=True,
        help="Utility function to execute",
        dest="function"
    )

    utility_functions: set[UtilityFunction] = {InviteURLGenerator()}

    utility_function: UtilityFunction
    for utility_function in utility_functions:
        utility_function.attach_to_parser(function_subparsers)

    parsed_args: Namespace = arg_parser.parse_args()

    for utility_function in utility_functions:
        if parsed_args.function == utility_function.NAME:
            utility_function.run(parsed_args)
            arg_parser.exit(status=0)

    arg_parser.error(f"Unknown function: {parsed_args.function!r}")
