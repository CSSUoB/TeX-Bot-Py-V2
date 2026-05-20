"""Functions to enable interaction with MSL based SU websites."""

import logging
from typing import TYPE_CHECKING, override

import aiohttp

from config import settings
from utils import GLOBAL_SSL_CONTEXT

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from http.cookies import Morsel
    from logging import Logger
    from typing import Final


__all__: "Sequence[str]" = ("ORGANISATION_ADMIN_URL", "SGF_LANDING_URL", "SGF_URL", "su_platform_client")


logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

ORGANISATION_ID: "Final[str]" = settings["ORGANISATION_ID"]

ORGANISATION_ADMIN_URL: "Final[str]" = (
    f"https://www.guildofstudents.com/organisation/admin/{ORGANISATION_ID}/"
)

SGF_URL: "Final[str]" = f"https://www.guildofstudents.com/sgf/{ORGANISATION_ID}/"
SGF_LANDING_URL: "Final[str]" = f"{SGF_URL}/Landing/Member"


class SUPlatformClient:
    """A client for making authenticated requests to the SU platform."""

    @override
    def __init__(self) -> None:
        self.headers: Mapping[str, str] = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        self.cookies: Mapping[str, str] = {
            ".AspNet.SharedCookie": settings["SU_PLATFORM_ACCESS_COOKIE"],
        }

    def set_cookies(self, cookies: "Mapping[str, str]") -> None:
        """Set the SU platform access cookie."""
        self.cookies = cookies

    def set_cookie(self, cookie_name: str, cookie_value: str) -> None:
        """Set a specific cookie in the SU platform access cookie."""
        if cookie_name in self.cookies:
            new_cookies: dict[str, str] = dict(self.cookies)
            new_cookies[cookie_name] = cookie_value
            self.cookies = new_cookies
            return

        self.cookies = {
            **self.cookies,
            cookie_name: cookie_value,
        }


    async def fetch_url_content(self, url: str) -> str:
        async with (
            aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as http_session,
            http_session.get(url=url, ssl=GLOBAL_SSL_CONTEXT) as http_response,
        ):
            returned_asp_cookie: Morsel[str] | None = http_response.cookies.get(
                ".AspNet.SharedCookie"
            )

            sgf_cookie: Morsel[str] | None = http_response.cookies.get("AntiForgery.Sgf")
            if sgf_cookie:
                self.set_cookie("AntiForgery.Sgf", sgf_cookie.value)
                logger.debug("AntiForgery.Sgf cookie updated from response.")

            if not returned_asp_cookie:
                return await http_response.text()

            if returned_asp_cookie.value != self.cookies[".AspNet.SharedCookie"]:
                logger.info("New SU platform access cookie given by server; updating local.")
                self.set_cookie(".AspNet.SharedCookie", returned_asp_cookie.value)
            return await http_response.text()


su_platform_client: "Final[SUPlatformClient]" = SUPlatformClient()
