from typing import Any, Collection, Self

from django.contrib.contenttypes.fields import GenericRelation  # type: ignore
from django.core.exceptions import FieldDoesNotExist  # type: ignore
from django.db import models  # type: ignore

from db.core.exceptions import UpdateFieldNamesError


class Async_Base_Queryset(models.QuerySet):
    def _create(self, kwargs: dict[str, Any]) -> Self:
        proxy_field_values: dict[str, Any] = {key: kwargs.pop(key) for key in set(kwargs.keys()) - self.model.get_proxy_field_names()}

        obj = self.model(**kwargs)

        proxy_field_name: str
        value: Any
        for proxy_field_name, value in proxy_field_values.items():
            setattr(obj, proxy_field_name, value)

        self._for_write = True

        return obj

    _create.queryset_only = False  # type: ignore

    # noinspection SpellCheckingInspection
    async def acreate(self, **kwargs) -> Self:
        obj: Self = self._create(kwargs)

        await obj.asave(force_insert=True, using=self.db)

        return obj

    def create(self, **kwargs) -> Self:
        obj: Self = self._create(kwargs)

        obj.save(force_insert=True, using=self.db)

        return obj


class Async_Base_Model(models.Model):
    """
        Asynchronous Base model that provides extra synchronous & asynchronous
        utility methods for all other models to use.

        This class is abstract so should not be instantiated or have a table
        made for it in the database (see
        https://docs.djangoproject.com/en/4.2/topics/db/models/#abstract-base-classes).
    """

    # objects: models.Manager = Async_Base_Queryset.as_manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs) -> None:
        set_proxy_field_keys: set[str] = set()

        key: str
        for key in kwargs.keys():
            if key in self.get_proxy_field_names():
                set_proxy_field_keys.add(key)

        set_proxy_fields: dict[str, Any] = {}
        for key in set_proxy_field_keys:
            set_proxy_fields[key] = kwargs.pop(key)

        super().__init__(*args, **kwargs)

        for key, value in set_proxy_fields.items():
            setattr(self, key, value)

    def _base_save(self, clean: bool) -> None:
        if clean:
            self.full_clean()

    async def abase_save(self, clean: bool = True, *args, **kwargs) -> None:
        """
            The asynchronous lowest level saving function that can bypass model
            cleaning (which will usually occur if save() is called), when
            recursive saving is required (E.g. within the update() method).
        """

        self._base_save(clean)

        await models.Model.asave(self, *args, **kwargs)

    def base_save(self, clean: bool = True, *args, **kwargs) -> None:
        """
            The lowest level saving function that can bypass model cleaning
            (which will usually occur if save() is called), when recursive
            saving is required (E.g. within the update() method).
        """

        self._base_save(clean)

        models.Model.save(self, *args, **kwargs)

    def _refresh_from_db(self, fields: set[str] | None, deep: bool) -> None:
        if deep:  # NOTE: Refresh any related fields/objects if requested
            if fields is None:
                fields = set()

            model_fields: set[models.Field] = {model_field for model_field in self._meta.get_fields() if
                                               model_field.name != "+"}

            update_fields: set[models.Field] = model_fields

            if fields:  # NOTE: Limit the fields to update by the provided list of field names
                update_fields = {update_field for update_field in update_fields if update_field.name in fields}

            if not update_fields:  # NOTE: Raise exception if none of the provided field names are valid fields for this model
                raise UpdateFieldNamesError(model_fields=model_fields, update_field_names=fields)

            else:
                updated_model: models.Model = self._meta.model.objects.get(id=self.id)

                for field in update_fields:
                    if field.is_relation and not isinstance(field, models.ManyToManyField) and not isinstance(
                            field,
                            models.ManyToManyRel
                    ) and not isinstance(
                        field, GenericRelation
                    ) and not isinstance(
                        field,
                        models.ManyToOneRel
                    ):  # NOTE: It is only possible to refresh related objects from one of these hard-coded field types
                        setattr(self, field.name, getattr(updated_model, field.name))

                    elif field.is_relation:  # BUG: Relation fields not of acceptable type are not refreshed
                        pass

    # noinspection SpellCheckingInspection
    async def arefresh_from_db(self, using: str | None = None, fields: Collection[str] | None = None, deep: bool = True) -> None:
        """
            Asynchronous custom implementation of refreshing in-memory objects
            from the database, which also updates any related fields on this
            object. The fields to update can be limited with the "fields"
            argument, and whether to update related objects or not can be
            specified with the "deep" argument.
        """

        if fields is not None and not isinstance(fields, set):  # NOTE: Remove duplicate field names from fields parameter
            fields = set(fields)

        await super().arefresh_from_db(using=using, fields=fields)

        self._refresh_from_db(fields, deep)

    def refresh_from_db(self, using: str | None = None, fields: Collection[str] | None = None, deep: bool = True) -> None:
        """
            Custom implementation of refreshing in-memory objects from the
            database, which also updates any related fields on this object. The
            fields to update can be limited with the "fields" argument, and
            whether to update related objects or not can be specified with the
            "deep" argument.
        """

        if fields is not None and not isinstance(fields, set):  # NOTE: Remove duplicate field names from fields parameter
            fields = set(fields)

        super().refresh_from_db(using=using, fields=fields)

        self._refresh_from_db(fields, deep)

    # noinspection SpellCheckingInspection
    async def asave(self, *args, **kwargs) -> None:
        """
            Asynchronously saves the current instance to the database, only
            after the model has been cleaned. This ensures any data in the
            database is valid, even if the data was not added via a ModelForm
            (E.g. data is added using the ORM API).
        """

        self.full_clean()

        await super().asave(*args, **kwargs)

    def save(self, *args, **kwargs) -> None:
        """
            Saves the current instance to the database, only after the model
            has been cleaned. This ensures any data in the database is valid,
            even if the data was not added via a ModelForm (E.g. data is added
            using the ORM API).
        """

        self.full_clean()

        super().save(*args, **kwargs)

    def _update(self, kwargs: dict[str, Any]) -> None:
        key: str
        value: Any
        for key, value in kwargs.items():
            if key not in self.get_proxy_field_names():
                try:
                    self._meta.get_field(key)
                except FieldDoesNotExist:
                    raise
            setattr(self, key, value)

    # noinspection SpellCheckingInspection
    async def aupdate(self, commit: bool = True, base_save: bool = False, clean: bool = True, using: str | None = None, **kwargs) -> None:
        """
            Asynchronously changes an in-memory object's values & save that object to the
            database all in one operation (based on Django's
            Queryset.bulk_update method).
        """

        self._update(kwargs)

        if commit:
            if base_save:  # NOTE: Use the base_save method of the object (to skip additional save functionality) and only clean the object if specified
                await self.abase_save(clean, using)

            else:  # NOTE: Otherwise use the normal full save method of the object
                await self.asave(using)

    def update(self, commit: bool = True, base_save: bool = False, clean: bool = True, using: str | None = None, **kwargs) -> None:
        """
            Changes an in-memory object's values & save that object to the
            database all in one operation (based on Django's
            Queryset.bulk_update method).
        """

        self._update(kwargs)

        if commit:
            if base_save:  # NOTE: Use the base_save method of the object (to skip additional save functionality) and only clean the object if specified
                self.base_save(clean, using)

            else:  # NOTE: Otherwise use the normal full save method of the object
                self.save(using)

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return set()
