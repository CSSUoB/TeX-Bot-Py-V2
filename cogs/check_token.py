"""Contains cog classes for token checking interactions."""



from collections.abc import Sequence

__all__: Sequence[str] = ()

import logging
from logging import Logger

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup

logger: Logger = logging.getLogger("TeX-Bot")


request_headers: dict[str, str] = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "0",
}
request_cookies: dict[str, str] = {
    ".ASPXAUTH": settings["MEMBERS_LIST_URL_SESSION_COOKIE"],
}
async with aiohttp.ClientSession(headers=request_headers, cookies=request_cookies) as http_session:  # noqa: E501, SIM117
    async with http_session.get(url=settings["MEMBERS_LIST_URL"]) as http_response:
        response_html: str = await http_response.text()

MEMBER_HTML_TABLE_IDS: Final[frozenset[str]] = frozenset(
    {
        "ctl00_Main_rptGroups_ctl05_gvMemberships",
        "ctl00_Main_rptGroups_ctl03_gvMemberships",
    },
)
table_id: str
for table_id in MEMBER_HTML_TABLE_IDS:
    parsed_html: bs4.Tag | bs4.NavigableString | None = BeautifulSoup(
        response_html,
        "html.parser",
    ).find(
        "table",
        {"id": table_id},
    )

    if parsed_html is None or isinstance(parsed_html, bs4.NavigableString):
        continue




