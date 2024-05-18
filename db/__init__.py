"""Contains the entire package required to run Django's ORM as a database connector."""

from collections.abc import Sequence

__all__: Sequence[str] = ()


import os

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "db._settings"


django_setup_error: RuntimeError
try:
    django.setup()
except RuntimeError as django_setup_error:
    if "populate() isn't reentrant" not in str(django_setup_error):
        raise
