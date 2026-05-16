"""Custom exception classes related to Django processes."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: "Sequence[str]" = ("UnknownDjangoError",)


from typing import override

from typed_classproperties import classproperty

from .base import BaseTeXBotError


class UnknownDjangoError(BaseTeXBotError, RuntimeError):
    """Exception class to raise when an unknown Django error occurs."""

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "An unknown Django error occurred."
