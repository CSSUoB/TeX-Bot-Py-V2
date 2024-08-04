"""Functions to enable interaction with Google Calendar API."""

from collections.abc import Sequence

__all__: Sequence[str] = ("GoogleCalendar",)


import datetime
import logging
from logging import Logger
from pathlib import Path
from typing import TYPE_CHECKING, Final

import anyio
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

if TYPE_CHECKING:
    from googleapiclient._apis.calendar.v3.resources import CalendarResource
    from googleapiclient._apis.calendar.v3.schemas import Events

SCOPES: Final[Sequence[str]] = ["https://www.googleapis.com/auth/calendar.readonly"]

logger: Final[Logger] = logging.getLogger("TeX-Bot")

class GoogleCalendar:
    """Class to define the Google Calendar API."""

    @staticmethod
    async def fetch_credentials() -> Credentials | None:
        """Fetch the credentials for the Google Calendar API."""
        credentials: Credentials | None = None

        if Path("token.json").exists():
            credentials = Credentials.from_authorized_user_file("token.json", SCOPES)  # type: ignore[no-untyped-call]
            logger.debug("Credentials loaded from token.json")

        if not credentials or not credentials.token_state.FRESH:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())  # type: ignore[no-untyped-call]
                logger.debug("Credentials refreshed")
            else:
                flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file="credentials.json", scopes=SCOPES,
                )
                credentials = flow.run_local_server(port=0)
                logger.debug("Attempted to fetch credentials")

            if not credentials:
                return None

            try:
                async with await anyio.open_file(file="token.json") as token:
                    await token.write(credentials.to_json())  # type: ignore[no-untyped-call]
            except Exception as error:
                logger.exception("Failed to write credentials to token.json")
                logger.debug(error.args)
                logger.debug(error.with_traceback)
                return None

        return credentials

    @staticmethod
    async def fetch_events() -> list[dict[str, str]] | None:
        """Fetch the events from the Google Calendar API."""
        credentials: Credentials | None = await GoogleCalendar.fetch_credentials()
        if not credentials:
            return None

        try:
            service: CalendarResource = build(
                serviceName="calendar",
                version="v3",
                credentials=credentials,
            )

            now: str = datetime.datetime.now(tz=datetime.UTC).isoformat()

            events: Events = (
                service.events().list(
                    calendarId="kg5v9k480jn2qahpmq33h8g7cs@group.calendar.google.com",
                    timeMin=now,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            if not events:
                return None

            events_list = events.get("items", [])

            if not events_list:
                return None

            formatted_events: list[dict[str, str]] = [{
                    "event_id": event["id"],
                    "event_title": event["summary"],
                    "start_dt": str(event["start"]),
                    "end_dt": str(event["end"]),
                }
                for event in events_list
            ]

        except HttpError as error:
            logger.debug(error)
            return None

        else:
            return formatted_events
