"""Removes invalid tables in MD files for correct linting."""

import itertools
import pickle
import re
from pathlib import Path
from re import Match
from typing import TYPE_CHECKING, Final, TextIO

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


# TODO: Turn this into finding the project root (similar to `test_utils.py`)
def get_readme_path() -> Path:
    """
    Return the directory that acts as the root of the project.

    The project root is defined as the directory that contains the README.md file.
    """
    readme_parent_directory: Path = Path(__file__).resolve()
    for _ in range(6):
        readme_parent_directory = readme_parent_directory.parent

        current_path: Path
        for current_path in readme_parent_directory.iterdir():
            if "README.md" in current_path.name:
                return current_path

    NO_README_PARENT_DIRECTORY_MESSAGE: Final[str] = "Could not locate README.md file."
    raise FileNotFoundError(NO_README_PARENT_DIRECTORY_MESSAGE)


def _get_next_invalid_table_line(file: TextIO, start_line_number: int = 1) -> int:
    if start_line_number < 1:
        INVALID_START_LINE_NUMBER_MESSAGE: Final[str] = (
            f"{start_line_number.__name__!r} must be an integer greater than or equal to 1."  # type: ignore[attr-defined]
        )
        raise ValueError(INVALID_START_LINE_NUMBER_MESSAGE)

    file.seek(0)

    next_invalid_table_line_number: int
    current_line: str
    for next_invalid_table_line_number, current_line in enumerate(file, start_line_number):
        if re.match(r"\| .+<br/>\* .", current_line):
            return next_invalid_table_line_number

    NO_INVALID_TABLES_FOUND_MESSAGE: Final[str] = "No invalid tables found."
    raise ValueError(NO_INVALID_TABLES_FOUND_MESSAGE)


def _find_boundary_line_numbers_of_table(file: TextIO, mid_table_line_number: int) -> tuple[int, int]:  # noqa: E501
    if mid_table_line_number < 1:
        INVALID_MID_TABLE_LINE_NUMBER_MESSAGE: Final[str] = (
            f"{mid_table_line_number.__name__!r} must be an integer "  # type: ignore[attr-defined]
            "greater than or equal to 1."
        )
        raise ValueError(INVALID_MID_TABLE_LINE_NUMBER_MESSAGE)

    start_of_table_line_number: int = mid_table_line_number
    end_of_table_line_number: int = mid_table_line_number

    if mid_table_line_number != 1:
        file.seek(0)
        # HACK: Fix how the file is being read in to reduce memory usage
        backwards_file_lines: Sequence[str] = tuple(file)[:(mid_table_line_number - 1) + 1]

        current_backwards_line_number: int
        for current_backwards_line_number in range(mid_table_line_number - 1, 1, -1):
            current_backwards_line_regex_match: Match[str] | None = re.match(
                r"\|--+\|",
                backwards_file_lines[current_backwards_line_number - 1]
            )
            if current_backwards_line_regex_match:
                start_of_table_line_number = current_backwards_line_number - 1
                break
        else:
            start_of_table_line_number = 1

    del current_backwards_line_regex_match
    del current_backwards_line_number
    del backwards_file_lines

    if mid_table_line_number != (len(file.readlines()) - 1) + 1:
        file.seek(0)
        # HACK: Fix how the file is being read in to reduce memory usage
        forwards_file_lines: Sequence[str] = tuple(file)[(mid_table_line_number + 1) - 1:]

        current_forwards_line_number: int
        for current_forwards_line_number in range(1, (len(forwards_file_lines) - 1) + 1):
            current_forwards_line_regex_match: Match[str] | None = re.match(
                r"\| .+\|",
                forwards_file_lines[current_forwards_line_number - 1]
            )
            if not current_forwards_line_regex_match:
                end_of_table_line_number = (
                    (current_forwards_line_number - 1)
                    + mid_table_line_number
                )
                break
        else:
            end_of_table_line_number = (len(file.readlines()) - 1) + 1

    return start_of_table_line_number, end_of_table_line_number


def remove_invalid_tables() -> None:
    """Remove all invalid tables within every markdown file in repository."""
    # TODO: Loop through all markdown files (store in pickled dict)
    # TODO: Loop through every table in every file
    readme_file: TextIO
    with get_readme_path().open("r", encoding="utf8") as readme_file:
        first_invalid_table_line: int = _get_next_invalid_table_line(readme_file)

        start_of_table_line_number: int
        end_of_table_line_number: int
        start_of_table_line_number, end_of_table_line_number = _find_boundary_line_numbers_of_table(  # noqa: E501
            readme_file,
            first_invalid_table_line
        )

        readme_lines: Sequence[str] = readme_file.readlines()

    with Path("original_readme.pkl").open("wb") as original_readme_file:
        pickle.dump(readme_lines, original_readme_file)

    fixed_readme_lines: Iterable[str] = itertools.chain(
        readme_lines[:start_of_table_line_number],
        readme_lines[end_of_table_line_number:]
    )

    with get_readme_path().open("w", encoding="utf8") as readme_file:
        readme_file.writelines(fixed_readme_lines)


def return_invalid_tables() -> None:
    """Return all markdown files to their original state before linting."""
    # TODO: Return all tables in all markdown files to original (from pickled dict)
    with Path("original_readme.pkl").open("rb") as original_readme_file:
        original_readme_lines: Sequence[str] = pickle.load(original_readme_file)  # noqa: S301

    with get_readme_path().open("w", encoding="utf8") as readme_file:
        readme_file.writelines(original_readme_lines)
