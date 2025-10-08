"""Contains the entire package required to run Django's ORM as a database connector."""

import os
from typing import TYPE_CHECKING

import django

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: Sequence[str] = ()


os.environ["DJANGO_SETTINGS_MODULE"] = "db._settings"


django_setup_error: RuntimeError
try:
    django.setup()
except RuntimeError as django_setup_error:
    if "populate() isn't reentrant" not in str(django_setup_error):
        raise
