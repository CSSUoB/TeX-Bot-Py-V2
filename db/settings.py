"""
Django settings for db project & core app within TeX-Bot-Py package.

Partially generated by 'django-admin startproject' using Django 4.2.1.
"""

from collections.abc import Sequence

__all__: Sequence[str] = ()

import inspect
from pathlib import Path

from config import settings

# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent

# NOTE: settings.py is called when setting up the mypy_django_plugin. When mypy runs no environment variables are set, so they should not be accessed
imported_by_pytest: bool = any(
    "mypy_django_plugin" in frame.filename
    for frame
    in inspect.stack()[1:]
    if not frame.filename.startswith("<")
)
if not imported_by_pytest:
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = settings.DISCORD_BOT_TOKEN


# Application definition

INSTALLED_APPS = ["django.contrib.contenttypes", "db.core.app_config.CoreConfig"]

MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]


# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "core.db",
    }
}


# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "Europe/London"

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
