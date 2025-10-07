from collections.abc import Awaitable, Callable, Iterable, Sequence
from typing import overload, override

from discord.commands.context import AutocompleteContext

__all__: Sequence[str] = ("Option", "OptionChoice", "option")

class Option: ...

class OptionChoice:
    @override
    def __init__(self, *, name: str, value: str | float) -> None: ...

@overload
def option[**P, **Q, T, T_context: AutocompleteContext](
    *,
    name: str,
    description: str,
    input_type: type[T],
    required: bool = ...,
    default: T = ...,
    choices: Iterable[OptionChoice] | Iterable[str] | Iterable[int] | Iterable[float] = ...,
    parameter_name: str = ...,
    autocomplete: Callable[
        [T_context],
        Awaitable[Iterable[OptionChoice] | Iterable[str]],
    ]
    | Callable[
        [T_context],
        Awaitable[Iterable[OptionChoice] | Iterable[str] | Iterable[int]],
    ] = ...,
) -> Callable[[Callable[P, Awaitable[None]]], Callable[Q, Awaitable[None]]]: ...
@overload
def option[**P, **Q, T_context: AutocompleteContext](
    *,
    name: str,
    description: str,
    input_type: type[str],
    parameter_name: str = ...,
    default: str = ...,
    choices: Iterable[OptionChoice] | Iterable[str] | Iterable[int] | Iterable[float] = ...,
    autocomplete: Callable[
        [T_context],
        Awaitable[Iterable[OptionChoice] | Iterable[str]],
    ]
    | Callable[
        [T_context],
        Awaitable[Iterable[OptionChoice] | Iterable[str] | Iterable[int]],
    ] = ...,
    required: bool = ...,
    min_length: int = ...,
    max_length: int = ...,
) -> Callable[[Callable[P, Awaitable[None]]], Callable[Q, Awaitable[None]]]: ...
