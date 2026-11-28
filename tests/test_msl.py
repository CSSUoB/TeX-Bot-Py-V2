"""Test suite for the features that depend upon your group's MSL website."""

__all__: Sequence[str] = (
    "TestCheckMSLAuthCookieIsSet",
    "TestCheckMSLIsConfigured",
    "TestSUPlatformAccessCookieCheckTask",
)

import asyncio
lazy from collections.abc import Awaitable, Callable, Sequence
lazy from pathlib import Path
lazy from typing import Final

import pytest
lazy from discord.ext.commands.errors import CheckAnyFailure

import config
from config._accessor import SettingsAccessor
from utils import CommandChecks
lazy from cogs.check_su_platform_authorisation import (
    CheckSUPlatformAuthorisationTaskCog,
    SUPlatformAccessCookieStatus,
)
lazy from utils import TeXBotBaseCog

type MSLSettingsApplier = Callable[[str | None, str | None], None]

# NOTE: A fabricated value, structured to satisfy the bot-token pattern:
# 24-26 characters, then 6, then 27-38.
VALID_BOT_TOKEN: Final[str] = "MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs"  # noqa: S105

VALID_MAIN_GUILD_ID: Final[int] = 1234567890123456789

VALID_ORGANISATION_ID: Final[str] = "1234"

VALID_AUTH_COOKIE: Final[str] = "a" * 600

REQUIRED_SETTINGS_YAML: Final[str] = (
    f"discord:\n  bot-token: {VALID_BOT_TOKEN}\n  main-guild-id: {VALID_MAIN_GUILD_ID}\n"
)


def _settings_yaml(organisation_id: str | None, auth_cookie: str | None) -> str:
    """Return a valid configuration holding only the given MSL settings."""
    msl_settings_yaml: str = "".join(
        f"    {setting_name}: '{setting_value}'\n"
        for setting_name, setting_value in (
            ("organisation-id", organisation_id),
            ("auth-cookie", auth_cookie),
        )
        if setting_value is not None
    )

    if not msl_settings_yaml:
        return REQUIRED_SETTINGS_YAML

    return f"{REQUIRED_SETTINGS_YAML}community-group:\n  msl:\n{msl_settings_yaml}"


@pytest.fixture(scope="module", autouse=True)
def _load_required_settings(tmp_path_factory: pytest.TempPathFactory) -> None:
    """
    Load a valid configuration before any cog is imported.

    Importing any cog loads every other one alongside it, several of which read the
    configuration as they are imported, so a valid configuration must already be loaded
    before the import can succeed at all.
    """
    CONFIG_FILE_PATH: Final[Path] = tmp_path_factory.mktemp("msl") / "tex-bot-deployment.yaml"
    CONFIG_FILE_PATH.write_text(REQUIRED_SETTINGS_YAML, encoding="utf-8")

    config.settings.reload(CONFIG_FILE_PATH)


@pytest.fixture()
def apply_msl_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MSLSettingsApplier:
    """Return a callable that loads a configuration holding only the given MSL settings."""

    def _apply_msl_settings(organisation_id: str | None, auth_cookie: str | None) -> None:
        config_file_path: Path = tmp_path / "tex-bot-deployment.yaml"
        config_file_path.write_text(
            _settings_yaml(organisation_id, auth_cookie), encoding="utf-8"
        )

        settings_accessor: SettingsAccessor = SettingsAccessor()
        settings_accessor.reload(config_file_path)

        monkeypatch.setattr("utils.msl.memberships.settings", settings_accessor)

    return _apply_msl_settings


PARTIAL_MSL_SETTINGS: Final[Sequence[tuple[str | None, str | None]]] = (
    (None, None),
    (VALID_ORGANISATION_ID, None),
    (None, VALID_AUTH_COOKIE),
)


class TestCheckMSLIsConfigured:
    """Test case for the command check that requires both MSL settings to be set."""

    @staticmethod
    def _run_check() -> Awaitable[bool]:
        """Run the MSL command check, as it would be run before a command is executed."""

        @CommandChecks.check_msl_is_configured
        async def _command(_cog: TeXBotBaseCog) -> None:
            pass

        MSL_CHECK: Final[Callable[[object], Awaitable[bool]]] = _command.__commands_checks__[0]  # type: ignore[attr-defined]

        return MSL_CHECK(None)

    @classmethod
    @pytest.mark.parametrize(("organisation_id", "auth_cookie"), PARTIAL_MSL_SETTINGS)
    def test_a_command_is_refused_without_both_msl_settings(
        cls,
        apply_msl_settings: MSLSettingsApplier,
        organisation_id: str | None,
        auth_cookie: str | None,
    ) -> None:
        """Test that a partial MSL configuration is still valid, but stops the command."""
        apply_msl_settings(organisation_id, auth_cookie)

        with pytest.raises(CheckAnyFailure) as check_failure:
            asyncio.run(cls._run_check())

        assert CommandChecks.is_msl_is_configured_failure(check_failure.value.checks[0])  # type: ignore[arg-type]

    @classmethod
    def test_a_command_runs_with_both_msl_settings(
        cls, apply_msl_settings: MSLSettingsApplier
    ) -> None:
        """Test that setting both the organisation ID & cookie lets the command run."""
        apply_msl_settings(VALID_ORGANISATION_ID, VALID_AUTH_COOKIE)

        assert asyncio.run(cls._run_check()) is True


class TestCheckMSLAuthCookieIsSet:
    """Test case for the command check that requires only the MSL cookie to be set."""

    @staticmethod
    def _run_check() -> Awaitable[bool]:
        """Run the MSL cookie command check, as it would be run before a command."""

        @CommandChecks.check_msl_auth_cookie_is_set
        async def _command(_cog: TeXBotBaseCog) -> None:
            pass

        MSL_AUTH_COOKIE_CHECK: Final[Callable[[object], Awaitable[bool]]] = (
            _command.__commands_checks__[0]  # type: ignore[attr-defined]
        )

        return MSL_AUTH_COOKIE_CHECK(None)

    @classmethod
    @pytest.mark.parametrize("organisation_id", (None, VALID_ORGANISATION_ID))
    def test_a_command_is_refused_without_the_cookie(
        cls, apply_msl_settings: MSLSettingsApplier, organisation_id: str | None
    ) -> None:
        """Test that a command needing only the cookie is stopped when it is not set."""
        apply_msl_settings(organisation_id, None)

        with pytest.raises(CheckAnyFailure) as check_failure:
            asyncio.run(cls._run_check())

        assert CommandChecks.is_msl_auth_cookie_is_set_failure(
            check_failure.value.checks[0]  # type: ignore[arg-type]
        )

    @classmethod
    def test_a_command_runs_with_only_the_cookie(
        cls, apply_msl_settings: MSLSettingsApplier
    ) -> None:
        """
        Test that a command needing only the cookie runs without an organisation ID.

        Listing the organisations the cookie can reach is how the organisation ID is
        found, so requiring that ID first would block the way to finding it.
        """
        apply_msl_settings(None, VALID_AUTH_COOKIE)

        assert asyncio.run(cls._run_check()) is True


@pytest.fixture()
def cookie_status_requests(monkeypatch: pytest.MonkeyPatch) -> list[None]:
    """Return a record of each time the cookie check task asks the SU platform for status."""
    status_requests: list[None] = []

    async def _get_su_platform_access_cookie_status(
        _cog: CheckSUPlatformAuthorisationTaskCog,
    ) -> SUPlatformAccessCookieStatus:
        status_requests.append(None)
        return SUPlatformAccessCookieStatus.AUTHORISED

    monkeypatch.setattr(
        CheckSUPlatformAuthorisationTaskCog,
        "get_su_platform_access_cookie_status",
        _get_su_platform_access_cookie_status,
    )

    return status_requests


def _run_cookie_check_task() -> None:
    """Run a single iteration of the SU platform access cookie check task."""
    # NOTE: The task's own constructor would start the repeating task, so the cog is
    # created without it. The task never reaches for the running bot before the request
    # that is being recorded, so it does not need a connection to Discord.
    cog: CheckSUPlatformAuthorisationTaskCog = CheckSUPlatformAuthorisationTaskCog.__new__(
        CheckSUPlatformAuthorisationTaskCog
    )

    asyncio.run(
        CheckSUPlatformAuthorisationTaskCog.su_platform_access_cookie_check_task.coro(cog)
    )


class TestSUPlatformAccessCookieCheckTask:
    """Test case for the repeated task that checks the SU platform access cookie."""

    @staticmethod
    @pytest.mark.parametrize(("organisation_id", "auth_cookie"), PARTIAL_MSL_SETTINGS)
    def test_the_check_is_skipped_without_both_msl_settings(
        apply_msl_settings: MSLSettingsApplier,
        cookie_status_requests: list[None],
        organisation_id: str | None,
        auth_cookie: str | None,
    ) -> None:
        """Test that the task neither fails nor contacts the SU platform when not set up."""
        apply_msl_settings(organisation_id, auth_cookie)

        _run_cookie_check_task()

        assert not cookie_status_requests

    @staticmethod
    def test_the_check_runs_with_both_msl_settings(
        apply_msl_settings: MSLSettingsApplier, cookie_status_requests: list[None]
    ) -> None:
        """Test that the task checks the cookie once both MSL settings are set."""
        apply_msl_settings(VALID_ORGANISATION_ID, VALID_AUTH_COOKIE)

        _run_cookie_check_task()

        assert len(cookie_status_requests) == 1
