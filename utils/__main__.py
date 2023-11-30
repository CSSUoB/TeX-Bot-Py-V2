"""Command-line execution of the utils package."""

from argparse import ArgumentParser, Namespace
from collections.abc import Iterable, Sequence
from typing import Final

from utils import InviteURLGenerator, UtilityFunction


def main(argv: Sequence[str] | None = None, utility_functions: Iterable[UtilityFunction] | None = None) -> int:  # noqa: E501
    """Run this script as a CLI tool with argument parsing."""
    if utility_functions is None:
        utility_functions = set()

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

    utility_function: UtilityFunction
    for utility_function in utility_functions:
        utility_function.attach_to_parser(function_subparsers)

    parsed_args: Namespace = arg_parser.parse_args(argv)

    for utility_function in utility_functions:
        if parsed_args.function == utility_function.NAME:
            return utility_function.run(parsed_args)

    NO_FUNCTION_EXECUTED_MESSAGE: Final[str] = (
        "Valid function name provided, but not executed."
    )
    raise RuntimeError(NO_FUNCTION_EXECUTED_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main(utility_functions={InviteURLGenerator()}))
