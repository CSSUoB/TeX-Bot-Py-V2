import datetime
from collections.abc import Awaitable, Callable, Iterable, Sequence
from typing import Literal

from discord.abc import Snowflake
from discord.commands.context import AutocompleteContext
from discord.commands.options import OptionChoice
from discord.permissions import Permissions

__all__: Sequence[str] = (
    "basic_autocomplete",
    "format_dt",
    "get",
    "oauth_url",
    "sleep_until",
    "utcnow",
)

type Values = Iterable[OptionChoice] | Iterable[str]
type ValuesWithInt = Values | Iterable[int]
type AllValuesWithInt = ValuesWithInt | Awaitable[ValuesWithInt]

def basic_autocomplete[T_context: AutocompleteContext](
    values: AllValuesWithInt | Callable[[T_context], AllValuesWithInt],
) -> Callable[[T_context], Awaitable[Values]]: ...
def get[T](iterable: Iterable[T], **attrs: object) -> T | None: ...
def utcnow() -> datetime.datetime: ...
def format_dt(
    dt: datetime.datetime, /, style: Literal["f", "F", "d", "D", "t", "T", "R"] | None = ...
) -> str: ...
def oauth_url(
    client_id: int | str,
    *,
    permissions: Permissions = ...,
    guild: Snowflake = ...,
    redirect_uri: str = ...,
    scopes: Iterable[str] = ...,
    disable_guild_select: bool = ...,
) -> str: ...
async def sleep_until[T](when: datetime.datetime, result: T | None = ...) -> T | None: ...
