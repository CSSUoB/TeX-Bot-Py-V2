from collections.abc import Sequence

__all__: Sequence[str] = (
    "EnvVariableDeleter",
    "FileTemporaryDeleter",
    "TemporarySettingsKeyReplacer",
)

import hashlib
import os
from pathlib import Path
from types import TracebackType
from typing import Final

import git

from config import settings


class EnvVariableDeleter:
    """
    Context manager that deletes the given environment variable.

    The given environment variable is removed from both
    the system environment variables list,
    and the .env file in this project's root directory.
    """

    def __init__(self, env_variable_name: str) -> None:
        """Store the current state of any instances of the stored environment variable."""
        self.env_variable_name: str = env_variable_name

        PROJECT_ROOT: Final[str | git.PathLike | None] = git.Repo(
            ".", search_parent_directories=True
        ).working_tree_dir
        if PROJECT_ROOT is None:
            NO_ROOT_DIRECTORY_MESSAGE: Final[str] = "Could not locate project root directory."
            raise FileNotFoundError(NO_ROOT_DIRECTORY_MESSAGE)

        self.env_file_path: Path = PROJECT_ROOT / Path(".env")
        self.old_env_value: str | None = os.environ.get(self.env_variable_name)

    def __enter__(self) -> None:
        """Delete all stored instances of the stored environment variable."""
        if self.env_file_path.is_file():
            self.env_file_path = self.env_file_path.rename(
                self.env_file_path.parent / Path(".env.original"),
            )

        if self.old_env_value is not None:
            del os.environ[self.env_variable_name]

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:  # noqa: E501
        """Restore the deleted environment variable to its previous states."""
        if self.env_file_path.is_file():
            self.env_file_path.rename(self.env_file_path.parent / Path(".env"))

        if self.old_env_value is not None:
            os.environ[self.env_variable_name] = self.old_env_value


class TemporarySettingsKeyReplacer:  # TODO: Delete if has no uses
    """Context manager that temporarily replaces the value at the given settings key."""

    NOT_SET: Final[object] = object()

    @classmethod
    def _get_old_settings_value(cls, settings_key_name: str) -> object:
        try:
            return settings[settings_key_name]
        except KeyError:
            return cls.NOT_SET

    def __init__(self, settings_key_name: str, new_settings_value: object) -> None:
        """Store the current state of the settings value if it exists."""
        self.settings_key_name: str = settings_key_name
        self.new_settings_value: object = new_settings_value

        self.old_settings_value: object = self._get_old_settings_value(
            self.settings_key_name,
        )

    def __enter__(self) -> None:
        """Replace the settings value with the new value provided."""
        # noinspection PyProtectedMember
        settings._settings[self.settings_key_name] = self.new_settings_value  # noqa: SLF001

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:  # noqa: E501
        """Restore the replaced settings value with the original value if it existed."""
        if self.old_settings_value is self.NOT_SET:
            # noinspection PyProtectedMember
            settings._settings.pop(self.settings_key_name)  # noqa: SLF001

        else:
            # noinspection PyProtectedMember
            settings._settings[self.settings_key_name] = self.old_settings_value  # noqa: SLF001


class FileTemporaryDeleter:
    """
    Context manager that temporarily deletes the file at the given file path.

    The file at the given file path is restored after the context manager exits.
    """

    def __init__(self, file_path: Path) -> None:
        """Store the given file path to delete."""
        self.file_path: Path = file_path
        self._temp_file_path: Path | None = None

    def __enter__(self) -> None:
        """Delete the file at the stored file path if that file actually exists."""
        if self._temp_file_path is not None:
            ALREADY_DELETED_MESSAGE: Final[str] = (
                "Given file path has already been deleted by this context manager."
            )
            raise RuntimeError(ALREADY_DELETED_MESSAGE)

        if self.file_path.is_file():
            new_file_path: Path = self.file_path.parent / (
                f"{self.file_path.name}."
                f"{
                    hashlib.sha1(
                        str(self.file_path.resolve(strict=False)).encode(),
                        usedforsecurity=False,
                    ).hexdigest()[:10]
                }-"
                f"invalid"
            )

            if new_file_path.exists():
                CANNOT_DELETE_FILE_MESSAGE: Final[str] = (
                    "Cannot delete file at given file path: "
                    "file already exists at temporary file path."
                )
                raise RuntimeError(CANNOT_DELETE_FILE_MESSAGE)

            self.file_path.replace(new_file_path)
            self._temp_file_path = new_file_path

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:  # noqa: E501
        """Restore the deleted file at the stored file path."""
        if self._temp_file_path is not None:
            if not self._temp_file_path.exists():
                TEMPORARY_FILE_PATH_NOT_SAVED_CORRECTLY_MESSAGE: Final[str] = (
                    "Cannot restore the deleted file, "
                    "because the temporary file path was not stored correctly."
                )
                raise RuntimeError(TEMPORARY_FILE_PATH_NOT_SAVED_CORRECTLY_MESSAGE)

            self._temp_file_path.replace(self.file_path)
