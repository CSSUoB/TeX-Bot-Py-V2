"""Removes invalid tables in MD files for correct linting."""

import re
import shutil
from argparse import ArgumentParser, Namespace
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TextIO

from git import Repo

if TYPE_CHECKING:
    from os import PathLike


def _get_project_root() -> Path:
    project_root: Path = Path(__file__).resolve()

    for _ in range(8):
        project_root = project_root.parent

        if any(path.name.startswith("README.md") for path in project_root.iterdir()):
            return project_root

    NO_ROOT_DIRECTORY_MESSAGE: Final[str] = "Could not locate project root directory."
    raise FileNotFoundError(NO_ROOT_DIRECTORY_MESSAGE)


def _remove_any_invalid_tables(original_file_path: Path) -> None:
    table_lines: MutableSequence[int] = []
    custom_formatted_table_lines: MutableSequence[int] = []

    original_file: TextIO
    with original_file_path.open("r") as original_file:
        line_number: int
        line: str
        for line_number, line in enumerate(original_file, 1):
            if re.match(r"\|(?:( .+)|-+)\|", line):
                table_lines.append(line_number)

                if re.match(r"\| .+<br/>\* .", line):
                    custom_formatted_table_lines.append(line_number)

    if custom_formatted_table_lines and not table_lines:
        INCONSISTENT_TABLE_LINES_MESSAGE: Final[str] = (
            "Found custom-formatted table lines without any normal table lines."
        )
        raise RuntimeError(INCONSISTENT_TABLE_LINES_MESSAGE)

    if not table_lines:
        return

    temp_file_path: Path = shutil.copy2(
        original_file_path,
        original_file_path.parent / f"{original_file_path.name}.original"
    )
    new_file_path = original_file_path
    original_file_path = temp_file_path
    del temp_file_path

    with original_file_path.open("r") as original_file:
        new_file: TextIO
        with new_file_path.open("w") as new_file:
            def write_table_if_not_custom_formatted(write_table_line_number: int, *, is_newline: bool = False) -> None:  # noqa: E501
                write_table_lines: MutableSequence[str] = []
                while write_table_line_number in table_lines or is_newline:
                    is_newline = False

                    if write_table_line_number in custom_formatted_table_lines:
                        return

                    write_table_lines.append(original_file.readline())
                    write_table_line_number += 1

                write_table_line: str
                for write_table_line in write_table_lines:
                    new_file.write(write_table_line)

            line_number = 1
            at_end_of_original_file: bool = False
            while not at_end_of_original_file:
                current_position: int = original_file.tell()
                line = original_file.readline()
                at_end_of_original_file = not line

                if line:
                    if line_number not in table_lines and line != "\n":
                        new_file.write(line)
                    elif line == "\n":
                        if line_number + 1 not in table_lines:
                            new_file.write(line)
                        else:
                            original_file.seek(current_position)
                            _ = original_file.readline()
                            original_file.seek(current_position)
                            write_table_if_not_custom_formatted(line_number, is_newline=True)
                    else:
                        original_file.seek(current_position)
                        _ = original_file.readline()
                        original_file.seek(current_position)
                        write_table_if_not_custom_formatted(line_number, is_newline=False)

                line_number += 1


def remove_invalid_tables() -> None:
    """Remove all invalid tables within every markdown file in repository."""
    project_root: Path = _get_project_root()

    file_entry: tuple[str | PathLike[str], Any]
    for file_entry in Repo(project_root).index.entries:
        file_path: Path = project_root / file_entry[0]

        if not file_path.is_file() or not file_path.exists():
            continue

        original_file_path: Path = file_path.parent / f"{file_path.name}.original"
        if original_file_path.exists():
            ORIGINAL_FILE_ALREADY_EXISTS_MESSAGE: str = (
                "Cannot remove custom-formatted tables from markdown files: "
                f"{original_file_path} already exists. "
                f"Use `python {Path(__file__).name} --restore` to first restore the files "
                "to their original state"
            )
            raise FileExistsError(ORIGINAL_FILE_ALREADY_EXISTS_MESSAGE)

        if file_path.suffix == ".md":
            _remove_any_invalid_tables(file_path)


def restore_invalid_tables() -> None:
    """Return all markdown files to their original state before linting."""
    project_root: Path = _get_project_root()

    file_entry: tuple[str | PathLike[str], Any]
    for file_entry in Repo(project_root).index.entries:
        file_path: Path = project_root / file_entry[0]

        if not file_path.is_file() or not file_path.exists():
            continue

        file_is_temporary_original: bool = (
                len(file_path.suffixes) == 2
                and ".md" in file_path.suffixes
                and ".original" in file_path.suffixes
        )
        if file_is_temporary_original:
            file_path.rename(file_path.parent / file_path.stem)


def main(argv: Sequence[str] | None = None) -> int:
    """Run this script as a CLI tool with argument parsing."""
    arg_parser: ArgumentParser = ArgumentParser(
        description="Remove or restore custom formatted tables from all markdown files"
    )
    arg_parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore any custom-formatted tables from the original file"
    )
    arg_parser.add_argument(
        "--remove",
        action="store_false",
        dest="restore",
        help=(
            "Override the `--restore` flag "
            "and explicitly declare to remove any custom-formatted tables"
        )
    )

    parsed_args: Namespace = arg_parser.parse_args(argv)

    if not parsed_args.restore:
        remove_invalid_tables()
    else:
        restore_invalid_tables()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
