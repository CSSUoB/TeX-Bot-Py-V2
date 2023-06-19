from typing import Collection

from django.db.models import Field

from exceptions import BaseError


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
