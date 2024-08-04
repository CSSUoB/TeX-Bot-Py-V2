import os

os.environ["DJANGO_SETTINGS_MODULE"] = "db.settings"

from django.core import management

management.call_command("makemigrations")
