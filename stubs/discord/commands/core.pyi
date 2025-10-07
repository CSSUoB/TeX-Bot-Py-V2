from collections.abc import Awaitable, Callable, Sequence

__all__: Sequence[str] = (
    "ApplicationCommand",
    "MessageCommand",
    "SlashCommand",
    "SlashCommandGroup",
    "UserCommand",
    "application_command",
    "command",
    "message_command",
    "slash_command",
    "user_command",
)

from typing import override

def slash_command[**P](
    *,
    description: str,
    name: str = ...,
) -> Callable[[Callable[P, Awaitable[None]]], SlashCommand]: ...
def user_command[**P](
    *, name: str = ..., description: str = ...
) -> Callable[[Callable[P, Awaitable[None]]], UserCommand]: ...
def message_command[**P](
    *, name: str = ..., description: str = ...
) -> Callable[[Callable[P, Awaitable[None]]], MessageCommand]: ...
def application_command[**P](
    *, description: str, name: str = ...
) -> Callable[[Callable[P, Awaitable[None]]], ApplicationCommand]: ...
def command[**P](
    *, description: str, name: str = ...
) -> Callable[[Callable[P, Awaitable[None]]], ApplicationCommand]: ...

class ApplicationCommand:
    qualified_name: str

class SlashCommand(ApplicationCommand): ...
class UserCommand(ApplicationCommand): ...
class MessageCommand(ApplicationCommand): ...

class SlashCommandGroup(ApplicationCommand):
    @override
    def __init__(self, name: str, description: str) -> None: ...
    def command[**P, T: ApplicationCommand](
        self, cls: type[T] = ..., *, name: str, description: str
    ) -> Callable[[Callable[P, Awaitable[None]]], T]: ...
