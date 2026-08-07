"""
Reading, writing & error-reporting for the raw deployment configuration file.

This module owns every interaction with `tex-bot-deployment.yaml` as a *document*:
locating it, parsing it while retaining its comments & formatting, writing it back
atomically, and mapping validation failures onto the lines that caused them.

It deliberately knows nothing about what any individual setting means;
the shape & meaning of the configuration is declared solely within `config._schema`.
"""

import io
import logging
import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING, override

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError

from exceptions import InvalidSettingsFileError, SettingsFileNotFoundError

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from logging import Logger
    from typing import Final, Self

    from pydantic import ValidationError


__all__: "Sequence[str]" = (
    "SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME",
    "SettingsDocument",
    "get_settings_file_path",
)


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

PROJECT_ROOT: "Final[Path]" = Path(__file__).parent.parent.resolve()

DEFAULT_SETTINGS_FILE_NAME: "Final[str]" = "tex-bot-deployment.yaml"

SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME: "Final[str]" = "TEX_BOT_CONFIG_PATH"


def get_settings_file_path() -> Path:
    """
    Locate the deployment configuration file.

    The location is taken from the `TEX_BOT_CONFIG_PATH` environment variable if it is set,
    otherwise `tex-bot-deployment.yaml` alongside the project root is used.
    """
    RAW_SETTINGS_FILE_PATH: Final[str | None] = os.getenv(
        SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME
    )

    if RAW_SETTINGS_FILE_PATH:
        settings_file_path: Path = Path(RAW_SETTINGS_FILE_PATH).expanduser()
        if not settings_file_path.is_file():
            SETTINGS_FILE_FROM_ENVIRONMENT_NOT_FOUND_MESSAGE: str = (
                f"The path given by the "
                f"{SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME} environment variable "
                f"does not refer to an existing file: {str(settings_file_path)!r}."
            )
            raise SettingsFileNotFoundError(SETTINGS_FILE_FROM_ENVIRONMENT_NOT_FOUND_MESSAGE)

        return settings_file_path.resolve()

    default_settings_file_path: Path = PROJECT_ROOT / DEFAULT_SETTINGS_FILE_NAME
    if not default_settings_file_path.is_file():
        NO_SETTINGS_FILE_MESSAGE: str = (
            f"No configuration file was found. Create a {DEFAULT_SETTINGS_FILE_NAME!r} file "
            f"within {str(PROJECT_ROOT)!r}, or set the "
            f"{SETTINGS_FILE_PATH_ENVIRONMENT_VARIABLE_NAME} environment variable "
            f"to the location of your configuration file."
        )
        raise SettingsFileNotFoundError(NO_SETTINGS_FILE_MESSAGE)

    return default_settings_file_path.resolve()


def _create_yaml_parser() -> YAML:
    """Create a YAML parser that retains comments & formatting when writing documents back."""
    yaml_parser: YAML = YAML()  # NOTE: Defaults to round-trip mode
    yaml_parser.preserve_quotes = True
    # NOTE: Without a generous line width, writing a document back would re-wrap any long
    # values it contains, producing spurious changes within otherwise untouched sections.
    yaml_parser.width = 4096

    return yaml_parser


class SettingsDocument:
    """
    A single deployment configuration file, held as a comment-preserving document.

    Holding the parsed document (rather than only the values taken from it) allows
    individual settings to be rewritten without discarding the comments, ordering &
    formatting of the file that a human wrote.
    """

    @override
    def __init__(self, file_path: Path, raw: "CommentedMap") -> None:
        """Initialise a configuration document already parsed from the given file path."""
        self._file_path: Path = file_path
        self._raw: CommentedMap = raw

    @classmethod
    def load(cls, file_path: Path | None = None) -> "Self":
        """Locate & parse the deployment configuration file."""
        RESOLVED_FILE_PATH: Final[Path] = (
            get_settings_file_path() if file_path is None else file_path
        )

        # NOTE: `get_settings_file_path()` has already checked that the file it returns
        # exists, but an explicitly given path has not been checked by anything. Checking
        # here keeps every failure to read the configuration reportable as one error type.
        if not RESOLVED_FILE_PATH.is_file():
            EXPLICIT_SETTINGS_FILE_NOT_FOUND_MESSAGE: str = (
                f"No configuration file exists at {str(RESOLVED_FILE_PATH)!r}."
            )
            raise SettingsFileNotFoundError(EXPLICIT_SETTINGS_FILE_NOT_FOUND_MESSAGE)

        raw_file_contents: str = RESOLVED_FILE_PATH.read_text(encoding="utf-8")

        yaml_parse_error: YAMLError
        try:
            # NOTE: Annotated as `object` because an arbitrary YAML file need not contain a
            # mapping at its top level: an empty file parses to `None`, and a file holding
            # only a scalar or a sequence parses to that value.
            raw: object = _create_yaml_parser().load(raw_file_contents)
        except YAMLError as yaml_parse_error:
            INVALID_YAML_MESSAGE: str = (
                f"{RESOLVED_FILE_PATH.name} is not a valid YAML file: {yaml_parse_error}"
            )
            raise InvalidSettingsFileError(INVALID_YAML_MESSAGE) from yaml_parse_error

        if raw is None:
            EMPTY_SETTINGS_FILE_MESSAGE: str = f"{RESOLVED_FILE_PATH.name} is empty."
            raise InvalidSettingsFileError(EMPTY_SETTINGS_FILE_MESSAGE)

        # NOTE: Checking for `CommentedMap` (rather than merely `dict`) also guarantees the
        # presence of the `lc` line-comment data that `line_number_of()` relies upon.
        if not isinstance(raw, CommentedMap):
            NOT_A_MAPPING_MESSAGE: str = (
                f"{RESOLVED_FILE_PATH.name} must contain a mapping of configuration "
                f"settings at its top level, but contains "
                f"{type(raw).__name__} instead."
            )
            raise InvalidSettingsFileError(NOT_A_MAPPING_MESSAGE)

        return cls(file_path=RESOLVED_FILE_PATH, raw=raw)

    @property
    def file_path(self) -> Path:
        """The location of the file this document was parsed from."""
        return self._file_path

    @property
    def raw(self) -> "CommentedMap":
        """
        The parsed document, retaining the comments & formatting of the original file.

        Mutating this mapping does not write anything to disk;
        `write()` must be called to persist any changes made.
        """
        return self._raw

    def contains(self, key_path: "Sequence[str]") -> bool:
        """Whether the given sequence of keys is written within this document."""
        node: object = self._raw

        key: str
        for key in key_path:
            if not isinstance(node, dict) or key not in node:
                return False

            node = node[key]

        return True

    def set_value(self, key_path: "Sequence[str]", value: object) -> None:
        """
        Write the given value at the given sequence of keys, creating any absent sections.

        Nothing is written to disk until `write()` is called.
        """
        if not key_path:
            EMPTY_KEY_PATH_MESSAGE: str = "A setting to change must be named."
            raise ValueError(EMPTY_KEY_PATH_MESSAGE)

        node: CommentedMap = self._raw

        key: str
        for key in key_path[:-1]:
            if key not in node:
                node[key] = CommentedMap()

            child_node: object = node[key]
            if not isinstance(child_node, CommentedMap):
                NOT_A_SECTION_MESSAGE: str = (
                    f"{self._file_path.name} cannot hold the setting "
                    f"{':'.join(key_path)!r}, because {key!r} is not a section."
                )
                raise InvalidSettingsFileError(NOT_A_SECTION_MESSAGE)

            node = child_node

        node[key_path[-1]] = value

    def unset_value(self, key_path: "Sequence[str]") -> bool:
        """
        Remove the given sequence of keys, reporting whether it was written at all.

        Any section left empty is kept, rather than being removed alongside the setting,
        because a section may be required to be present even when it holds nothing.

        Nothing is written to disk until `write()` is called.
        """
        if not self.contains(key_path):
            return False

        node: object = self._raw

        key: str
        for key in key_path[:-1]:
            if TYPE_CHECKING:
                assert isinstance(node, dict)

            node = node[key]

        if TYPE_CHECKING:
            assert isinstance(node, dict)

        del node[key_path[-1]]

        return True

    def dump(self) -> str:
        """Serialise this document back into YAML, retaining comments & formatting."""
        output_buffer: io.StringIO = io.StringIO()
        _create_yaml_parser().dump(self._raw, output_buffer)

        return output_buffer.getvalue()

    def _permissions_of_existing_file(self) -> int | None:
        """Return the permission bits of this document's file, if it can be determined."""
        stat_error: OSError
        try:
            return stat.S_IMODE(self._file_path.stat().st_mode)
        except OSError as stat_error:
            logger.debug(
                "Could not read the permissions of %s (%s); "
                "the file will be written with the permissions a new file is given.",
                self._file_path,
                stat_error.strerror or stat_error,
            )
            return None

    @staticmethod
    def _write_privately(file_path: Path, contents: str) -> None:
        """
        Write the given contents into the given path, readable only by its owner.

        The configuration file holds the bot token & the MSL authentication cookie, so
        it must never exist (even momentarily, as the temporary file written below does)
        with the permissions a newly created file would otherwise be given.
        """
        file_descriptor: int = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)

        opened_file: io.TextIOWrapper
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as opened_file:
            opened_file.write(contents)

    def write(self) -> None:
        """
        Persist this document to disk, atomically where the filesystem allows it.

        The serialised document is written to a temporary file alongside the destination
        and then moved into place, so that a failure partway through writing cannot leave
        a truncated configuration file behind.

        Where that move is rejected, the document is written directly instead. This
        happens when the configuration file is an individually mounted file within a
        container, because a rename cannot replace a mount point. Writing directly is not
        atomic, but it is the only option available in that case; mounting the directory
        holding the configuration file, rather than the file itself, avoids it entirely.

        The permissions of the file being replaced are carried across onto the file
        replacing it, so that a deployment which has deliberately restricted who may read
        its configuration file does not silently have those restrictions lifted.
        """
        NEW_FILE_CONTENTS: Final[str] = self.dump()

        EXISTING_FILE_PERMISSIONS: Final[int | None] = self._permissions_of_existing_file()

        temporary_file_path: Path = self._file_path.with_name(
            f"{self._file_path.name}.{os.getpid()}.tmp"
        )

        try:
            self._write_privately(temporary_file_path, NEW_FILE_CONTENTS)

            if EXISTING_FILE_PERMISSIONS is not None:
                temporary_file_path.chmod(EXISTING_FILE_PERMISSIONS)

            replace_error: OSError
            try:
                # NOTE: `os.replace()` is atomic where the source & destination are located
                # upon the same filesystem, which writing the temporary file alongside the
                # destination guarantees.
                os.replace(temporary_file_path, self._file_path)  # noqa: PTH105
            except OSError as replace_error:
                logger.debug(
                    (
                        "Could not atomically replace %s (%s); "
                        "falling back to writing it in place."
                    ),
                    self._file_path,
                    replace_error.strerror or replace_error,
                )
                self._file_path.write_text(NEW_FILE_CONTENTS, encoding="utf-8")
        finally:
            temporary_file_path.unlink(missing_ok=True)

    def line_number_of(self, key_path: "Sequence[str | int]") -> int | None:
        """
        Return the line within the original file that the given sequence of keys refers to.

        Where the given keys cannot be fully resolved (because a required key is absent
        from the file, for example), the line of the deepest key that *could* be resolved
        is returned, so that an error can still be pointed at the relevant section.
        """
        node: object = self._raw
        deepest_known_line_number: int | None = None

        key: str | int
        for key in key_path:
            line_comments: object = getattr(node, "lc", None)
            NODE_CONTAINS_KEY: bool = bool(
                line_comments is not None
                and isinstance(node, (dict, list))
                and (key in node if isinstance(node, dict) else False)
            )
            if not NODE_CONTAINS_KEY:
                break

            if TYPE_CHECKING:
                assert isinstance(node, dict)

            LINE_NUMBER_OF_KEY: int | None = self._line_number_of_key(node, key)
            if LINE_NUMBER_OF_KEY is None:
                break

            deepest_known_line_number = LINE_NUMBER_OF_KEY
            node = node[key]

        return deepest_known_line_number

    @staticmethod
    def _line_number_of_key(node: "dict[object, object]", key: "str | int") -> int | None:
        """
        Return the line that the given key of the given mapping was parsed from.

        `None` is returned for a key that was added to the document rather than parsed
        from the file, because such a key has no line within the file to report. This
        happens whenever the `/config` command writes a setting for the first time.
        """
        key_position: object
        try:
            key_position = node.lc.key(key)  # type: ignore[attr-defined]
        except KeyError:
            return None

        if not isinstance(key_position, tuple):
            return None

        # NOTE: `lc.key()` reports a zero-indexed line, whereas humans (& every editor)
        # count the first line of a file as line 1.
        return int(key_position[0]) + 1

    def _format_single_error(self, key_path: "Sequence[str | int]", message: str) -> str:
        """Format a single validation failure, prefixed with the location that caused it."""
        LINE_NUMBER: Final[int | None] = self.line_number_of(key_path)

        LOCATION: Final[str] = (
            f"{self._file_path.name}:{LINE_NUMBER}"
            if LINE_NUMBER is not None
            else self._file_path.name
        )
        SETTING_NAME: Final[str] = (
            ":".join(str(key) for key in key_path) if key_path else "(whole file)"
        )

        return f"{LOCATION}  {SETTING_NAME}\n    {message}"

    def format_validation_error(self, validation_error: "ValidationError") -> str:
        """
        Render a validation failure into a message suitable for a human to act upon.

        Every reported failure is annotated with the line of the configuration file that
        caused it. The offending values themselves are deliberately excluded, so that
        secrets cannot leak into logs or into any message sent to a Discord channel.
        """
        formatted_errors: Iterator[str] = (
            self._format_single_error(
                key_path=single_error["loc"], message=single_error["msg"]
            )
            for single_error in validation_error.errors(include_input=False, include_url=False)
        )

        return "\n".join(formatted_errors)
