from collections.abc import Awaitable, Callable, Coroutine, Sequence

__all__: Sequence[str] = (
    "ApplicationCommand",
    "CommandCallback",
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

from typing import Protocol, overload, override

# NOTE: The undecorated function that a command runs when it is invoked.
class CommandCallback(Protocol):
    __name__: str

    def __call__(
        self, *args: object, **kwargs: object
    ) -> Coroutine[object, object, None]: ...

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
    callback: CommandCallback

class SlashCommand(ApplicationCommand): ...
class UserCommand(ApplicationCommand): ...
class MessageCommand(ApplicationCommand): ...

class SlashCommandGroup(ApplicationCommand):
    @override
    def __init__(self, name: str, description: str) -> None: ...
    # NOTE: Overloaded because omitting `cls` leaves `T` unsolvable, which resolves to
    # `Never` & silently removes every command within a group from type-checking.
    @overload
    def command[**P](
        self, *, name: str, description: str
    ) -> Callable[[Callable[P, Awaitable[None]]], SlashCommand]: ...
    @overload
    def command[**P, T: ApplicationCommand](
        self, cls: type[T], *, name: str, description: str
    ) -> Callable[[Callable[P, Awaitable[None]]], T]: ...
