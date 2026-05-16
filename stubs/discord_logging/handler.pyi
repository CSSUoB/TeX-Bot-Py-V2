import logging
from collections.abc import Mapping, Sequence
from typing import override

__all__: Sequence[str] = ("DiscordHandler",)

class DiscordHandler(logging.Handler):
    @override
    def __init__(
        self,
        service_name: str,
        webhook_url: str,
        colours: Mapping[int | None, int] = ...,
        emojis: Mapping[int | None, str] = ...,
        avatar_url: str | None = ...,
        rate_limit_retry: bool = ...,
        embed_line_wrap_threshold: int = ...,
        message_break_char: str | None = ...,
        discord_timeout: float = ...,
    ) -> None: ...
