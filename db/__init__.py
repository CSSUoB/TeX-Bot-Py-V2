"""Contains the entire package required to run Django's ORM as a database connector."""

import os

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "db._settings"
e: RuntimeError
try:
    django.setup()
except RuntimeError as e:
    if "populate() isn't reentrant" not in str(e):
        raise
