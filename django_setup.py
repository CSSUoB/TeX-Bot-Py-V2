"""Django setup for pytest-django integration."""

import os

import django
from django.conf import settings

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'db._settings')

# Configure Django if not already configured
if not settings.configured:
    django.setup()
