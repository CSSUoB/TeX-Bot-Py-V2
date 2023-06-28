"""
    Utility classes & functions provided for all models to use.
"""

import hashlib
import re
from typing import Any

from asgiref.sync import sync_to_async
from django.core.exceptions import FieldDoesNotExist
from django.core.validators import RegexValidator
from django.db import models


class AsyncBaseModel(models.Model):
    """
        Asynchronous Base model that provides extra synchronous & asynchronous
        utility methods for all other models to use.

        This class is abstract so should not be instantiated or have a table
        made for it in the database (see
        https://docs.djangoproject.com/en/stable/topics/db/models/#abstract-base-classes).
    """

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs) -> None:
        proxy_fields: dict[str, Any] = {field_name: kwargs.pop(field_name) for field_name in set(kwargs.keys()) & self.get_proxy_field_names()}

        super().__init__(*args, **kwargs)

        field_name: str
        value: Any
        for field_name, value in proxy_fields.items():
            setattr(self, field_name, value)

    def save(self, *args, **kwargs) -> None:
        """
            Saves the current instance to the database, only after the model
            has been cleaned. This ensures any data in the database is valid,
            even if the data was not added via a ModelForm (E.g. data is added
            using the ORM API).
        """

        self.full_clean()

        super().save(*args, **kwargs)

    def update(self, commit: bool = True, using: str | None = None, **kwargs) -> None:
        """
            Changes an in-memory object's values & save that object to the
            database all in one operation (based on Django's
            Queryset.bulk_update method).
        """

        unexpected_kwargs: set[str] = set()

        field_name: str
        for field_name in set(kwargs.keys()) - self.get_proxy_field_names():
            try:
                # noinspection PyUnresolvedReferences
                self._meta.get_field(field_name)
            except FieldDoesNotExist:
                unexpected_kwargs.add(field_name)

        if unexpected_kwargs:
            raise TypeError(f"{self._meta.model.name} got unexpected keyword arguments: {tuple(unexpected_kwargs)}")

        value: Any
        for field_name, value in kwargs.items():
            setattr(self, field_name, value)

        if commit:
            self.save(using)

    update.alters_data = True

    # noinspection SpellCheckingInspection
    async def aupdate(self, commit: bool = True, using: str | None = None, **kwargs) -> None:
        """
            Asyncronously changes an in-memory object's values & save that
            object to the database all in one operation (based on Django's
            Queryset.bulk_update method).
        """
        await sync_to_async(self.update)(commit=commit, using=using, **kwargs)

    aupdate.alters_data = True

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return set()


class HashedDiscordMember(AsyncBaseModel):
    """
        Abstract base model to represent a Discord server member (identified by
        their hashed Discord member ID). This base model is inherited by any
        other model that wishes to represent a Discord member having a state
        happened to them.

        This class is abstract so should not be instantiated or have a table
        made for it in the database (see
        https://docs.djangoproject.com/en/stable/topics/db/models/#abstract-base-classes).
    """

    hashed_member_id = models.CharField(
        "Hashed Discord Member ID",
        unique=True,
        null=False,
        blank=False,
        max_length=64,
        validators=[
            RegexValidator(
                r"\A[A-Fa-f0-9]{64}\Z",
                "hashed_member_id must be a valid sha256 hex-digest."
            )
        ]
    )

    class Meta:
        abstract = True

    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: \"{self.hashed_member_id}\">"

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "member_id":
            self.hashed_member_id = self.hash_member_id(value)
        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        return f"{self.hashed_member_id}"

    @staticmethod
    def hash_member_id(member_id: Any) -> str:
        """
            Hashes the provided member_id into the format that hashed_member_ids
            are stored in the database when new objects of this class are
            created.
        """

        if not isinstance(member_id, (str, int)) or not re.match(r"\A\d{17,20}\Z", str(member_id)):
            raise ValueError(f"\"{member_id}\" is not a valid Discord member ID (see https://docs.pycord.dev/en/stable/api/abcs.html#discord.abc.Snowflake.id)")

        return hashlib.sha256(str(member_id).encode()).hexdigest()

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return super().get_proxy_field_names() | {"member_id"}
