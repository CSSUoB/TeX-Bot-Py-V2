"""Base exception classes inherited by other custom exceptions used within this project."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "BaseTeXBotError",
    "BaseErrorWithErrorCode",
    "BaseDoesNotExistError",
)


import abc
from typing import Final

from classproperties import classproperty


class BaseTeXBotError(BaseException, abc.ABC):
    """Base exception parent class."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N802,N805
        """The message to be displayed alongside this exception class if none is provided."""  # noqa: D401

    def __init__(self, message: str | None = None) -> None:
        """Initialize a new exception with the given error message."""
        self.message: str = message or self.DEFAULT_MESSAGE

        super().__init__(self.message)

    def __repr__(self) -> str:
        """Generate a developer-focused representation of the exception's attributes."""
        formatted: str = self.message

        attributes: dict[str, object] = self.__dict__
        attributes.pop("message")
        if attributes:
            formatted += f""" ({
                ", ".join(
                    {
                        f"{attribute_name}={attribute_value!r}"
                        for attribute_name, attribute_value
                        in attributes.items()
                    }
                )
            })"""

        return formatted


class BaseErrorWithErrorCode(BaseTeXBotError, abc.ABC):
    """Base class for exception errors that have an error code."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def ERROR_CODE(cls) -> str:  # noqa: N802,N805
        """The unique error code for users to tell admins about an error that occurred."""  # noqa: D401


class BaseDoesNotExistError(BaseErrorWithErrorCode, ValueError, abc.ABC):
    """Exception class to raise when a required Discord entity is missing."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_COMMANDS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of commands that require this Discord entity.

        This set being empty could mean that all commands require this Discord entity,
        or no commands require this Discord entity.
        """  # noqa: D401
        return frozenset()

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_TASKS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of tasks that require this Discord entity.

        This set being empty could mean that all tasks require this Discord entity,
        or no tasks require this Discord entity.
        """  # noqa: D401
        return frozenset()

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    def DEPENDENT_EVENTS(cls) -> frozenset[str]:  # noqa: N802,N805
        """
        The set of names of event listeners that require this Discord entity.

        This set being empty could mean that all event listeners require this Discord entity,
        or no event listeners require this Discord entity.
        """  # noqa: D401
        return frozenset()

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @abc.abstractmethod
    def DOES_NOT_EXIST_TYPE(cls) -> str:  # noqa: N802,N805
        """The name of the Discord entity that this `DoesNotExistError` is associated with."""  # noqa: D401

    @classmethod
    def get_formatted_message(cls, non_existent_object_identifier: str) -> str:  # noqa: C901, PLR0912, PLR0915
        """
        Format the exception message with the dependants that require the non-existent object.

        The message will also state that the given Discord entity does not exist.
        """
        if not cls.DEPENDENT_COMMANDS and not cls.DEPENDENT_TASKS and not cls.DEPENDENT_EVENTS:
            NO_DEPENDANTS_MESSAGE: Final[str] = (
                "Cannot get formatted message when non-existent object has no dependants."
            )
            raise ValueError(NO_DEPENDANTS_MESSAGE)

        formatted_dependent_commands: str = ""

        if cls.DEPENDENT_COMMANDS:
            if len(cls.DEPENDENT_COMMANDS) == 1:
                formatted_dependent_commands += (
                    f"\"/{next(iter(cls.DEPENDENT_COMMANDS))}\" command"
                )
            else:
                index: int
                dependent_command: str
                for index, dependent_command in enumerate(cls.DEPENDENT_COMMANDS):
                    formatted_dependent_commands += f"\"/{dependent_command}\""

                    if index < len(cls.DEPENDENT_COMMANDS) - 2:
                        formatted_dependent_commands += ", "
                    elif index == len(cls.DEPENDENT_COMMANDS) - 2:
                        formatted_dependent_commands += " & "

                formatted_dependent_commands += " commands"

        if cls.DOES_NOT_EXIST_TYPE.strip().lower() == "channel":
            non_existent_object_identifier = f"#{non_existent_object_identifier}"

        partial_message: str = (
            f"\"{non_existent_object_identifier}\" {cls.DOES_NOT_EXIST_TYPE} must exist "
            f"in order to use the {formatted_dependent_commands}"
        )

        if cls.DEPENDENT_TASKS:
            formatted_dependent_tasks: str = ""

            if cls.DEPENDENT_COMMANDS:
                if not cls.DEPENDENT_EVENTS:
                    partial_message += " and the "
                else:
                    partial_message += ", the "

            if len(cls.DEPENDENT_TASKS) == 1:
                formatted_dependent_tasks += f"\"{next(iter(cls.DEPENDENT_TASKS))}\" task"
            else:
                dependent_task: str
                for index, dependent_task in enumerate(cls.DEPENDENT_TASKS):
                    formatted_dependent_tasks += f"\"{dependent_task}\""

                    if index < len(cls.DEPENDENT_TASKS) - 2:
                        formatted_dependent_tasks += ", "
                    elif index == len(cls.DEPENDENT_TASKS) - 2:
                        formatted_dependent_tasks += " & "

                formatted_dependent_tasks += " tasks"

            partial_message += formatted_dependent_tasks

        if cls.DEPENDENT_EVENTS:
            formatted_dependent_events: str = ""

            if cls.DEPENDENT_COMMANDS or cls.DEPENDENT_TASKS:
                partial_message += " and the "

            if len(cls.DEPENDENT_EVENTS) == 1:
                formatted_dependent_events += f"\"{next(iter(cls.DEPENDENT_EVENTS))}\" event"
            else:
                dependent_event: str
                for index, dependent_event in enumerate(cls.DEPENDENT_EVENTS):
                    formatted_dependent_events += f"\"{dependent_event}\""

                    if index < len(cls.DEPENDENT_EVENTS) - 2:
                        formatted_dependent_events += ", "
                    elif index == len(cls.DEPENDENT_EVENTS) - 2:
                        formatted_dependent_events += " & "

                formatted_dependent_events += " events"

            partial_message += formatted_dependent_events

        return f"{partial_message}."
