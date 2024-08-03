"""Functions to enable interaction with Google Calendar API."""

from collections.abc import Sequence

__all__: Sequence[str] = ("GoogleCalendar",)


import datetime
import logging
from logging import Logger
from pathlib import Path
from typing import Final

import anyio
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())  # type: ignore[no-untyped-call]
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                credentials = flow.run_local_server(port=0)

            if not credentials:
                return None

            async with await anyio.open_file("token.json") as token:
                await token.write(credentials.to_json())  # type: ignore[no-untyped-call]

        return credentials

    @staticmethod
    async def fetch_events() -> list[dict[str, str]]:
        """Fetch the events from the Google Calendar API."""
        credentials: Credentials | None = await GoogleCalendar.fetch_credentials()
        if not credentials:
            return None

        try:
            service = build(serviceName="calendar", version="v3", credentials=credentials)

            now: str = datetime.datetime.now().isoformat() + "Z"

            events = (
                service.events().list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            if not events:
                return None
            
            return events

        except HttpError as error:
            return None



