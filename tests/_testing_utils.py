import os
from pathlib import Path
from types import TracebackType
from typing import Final

import git


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

        PROJECT_ROOT: Final[str | git.PathLike | None] = (
            git.Repo(".", search_parent_directories=True).working_tree_dir
        )
        if PROJECT_ROOT is None:
            NO_ROOT_DIRECTORY_MESSAGE: Final[str] = "Could not locate project root directory."
            raise FileNotFoundError(NO_ROOT_DIRECTORY_MESSAGE)

        self.env_file_path: Path = PROJECT_ROOT / Path(".env")
        self.old_env_value: str | None = os.environ.get(self.env_variable_name)

    def __enter__(self) -> None:
        """Delete all stored instances of the stored environment variable."""
        if self.env_file_path.is_file():
            self.env_file_path = self.env_file_path.rename(
                self.env_file_path.parent / Path(".env.original")
            )

        if self.old_env_value is not None:
            del os.environ[self.env_variable_name]

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:  # noqa: E501
        """Restore the deleted environment variable to its previous states."""
        if self.env_file_path.is_file():
            self.env_file_path.rename(self.env_file_path.parent / Path(".env"))

        if self.old_env_value is not None:
            os.environ[self.env_variable_name] = self.old_env_value
