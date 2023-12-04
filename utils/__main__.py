"""Command-line execution of the utils package."""

from collections.abc import Sequence

__all__: Sequence[str] = ["utility_functions"]

from argparse import ArgumentParser, Namespace

from utils import InviteURLGenerator, UtilityFunction

arg_parser: ArgumentParser = ArgumentParser(
    prog="utils",
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
