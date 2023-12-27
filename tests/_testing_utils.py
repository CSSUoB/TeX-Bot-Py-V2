import os
from pathlib import Path
from types import TracebackType
from typing import Final


class EnvVariableDeleter:
    """
    Context manager that deletes the given environment variable.

    The given environment variable is removed from both
    the system environment variables list,
    and the .env file in this project's root directory.
    """

    @staticmethod
    def _get_project_root() -> Path:
        project_root: Path = Path(__file__).resolve()

        for _ in range(8):
            project_root = project_root.parent

            if any(path.name.startswith("README.md") for path in project_root.iterdir()):
                return project_root

        NO_ROOT_DIRECTORY_MESSAGE: Final[str] = "Could not locate project root directory."
        raise FileNotFoundError(NO_ROOT_DIRECTORY_MESSAGE)

    def __init__(self, env_variable_name: str) -> None:
        """Store the current state of any instances of the stored environment variable."""
        self.env_variable_name: str = env_variable_name
        self.PROJECT_ROOT: Final[Path] = self._get_project_root()

        self.env_file_path: Path = self.PROJECT_ROOT / Path(".env")
        self.old_env_value: str | None = os.environ.get(self.env_variable_name)

    def __enter__(self) -> None:
        """Delete all stored instances of the stored environment variable."""
        if self.env_file_path.is_file():
            self.env_file_path = self.env_file_path.rename(
                self.PROJECT_ROOT / Path(".env.original")
            )

        if self.old_env_value is not None:
            del os.environ[self.env_variable_name]

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:  # noqa: E501
        """Restore the deleted environment variable to its previous states."""
        if self.env_file_path.is_file():
            self.env_file_path.rename(self.PROJECT_ROOT / Path(".env"))

        if self.old_env_value is not None:
            os.environ[self.env_variable_name] = self.old_env_value
