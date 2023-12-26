import pytest
from typing import TYPE_CHECKING

from config import Settings

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


@pytest.fixture(autouse=True)
def make_settings_instance_instance(request: "FixtureRequest") -> None:
    PREVIOUS_SETTINGS_INSTANCE: Settings = Settings._instance

    if "no_independent_settings_instance" not in request.keywords:
        Settings._instance = None

    yield

    Settings._instance = PREVIOUS_SETTINGS_INSTANCE
