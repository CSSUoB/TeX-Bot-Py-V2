"""Functions to enable interaction with Google Calendar API."""

from collections.abc import Sequence

__all__: Sequence[str] = ("",)


import datetime
import os.path
from typing import Final

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES: Final[Sequence[str]] = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendar:

    async def fetch_credentials(self) -> Credentials:
        """Fetch the credentials for the Google Calendar API."""
        credentials: Credentials | None = None

        if os.path.exists("token.json"):
            credentials = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        if not credentials or not credentials.valid or (credentials.expired and credentials.refresh_token):
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                credentials = flow.run_local_server(port=0)
        
            with open("token.json", "w") as token:
                token.write(credentials.to_json())

        return credentials


