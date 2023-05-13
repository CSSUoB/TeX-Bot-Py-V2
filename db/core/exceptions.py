import abc
from typing import Collection

from django.db.models import Field  # type: ignore


class BaseError(Exception, abc.ABC):
    # noinspection PyPropertyDefinition
    @classmethod  # type: ignore
    @property
    @abc.abstractmethod
    def DEFAULT_MESSAGE(cls) -> str:
        raise NotImplementedError

    @property
    def message(self) -> str:
        raise NotImplementedError

    @message.setter
    @abc.abstractmethod
    def message(self, value: str) -> None:
        raise NotImplementedError

    def __init__(self, message: str | None = None) -> None:
        self.message: str = message or self.DEFAULT_MESSAGE

        super().__init__(self.message)

    def __repr__(self) -> str:
        formatted: str = self.message

        attributes: set[str] = set(self.__dict__)
        attributes.discard("message")
        if attributes:
            formatted += f""" ({", ".join({f"{attribute=}" for attribute in attributes})})"""

        return formatted


class UpdateFieldNamesError(ValueError, BaseError):
    """
        Provided field names do not match any of the fields within the given
        model.
    """

    DEFAULT_MESSAGE = "Model's fields does not contain any of the requested update field names."  # TODO: Better default message

    def __init__(self, message: str | None = None, model_fields: Collection[Field] | None = None, update_field_names: Collection[str] | None = None) -> None:
        self.model_fields: set[Field] = set()
        if model_fields:
            self.model_fields = set(model_fields)

        self.update_field_names: set[str] = set()
        if update_field_names:
            self.update_field_names = set(update_field_names)

        super().__init__(message)
