"""Pytest configuration and fixtures for the test suite."""

import os

import django

# Configure Django settings before importing anything else
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db._settings")
django.setup()
