"""Custom exception classes related to Django processes."""

from collections.abc import Sequence

__all__: Sequence[str] = ("UnknownDjangoError",)


from typing import override

from classproperties import classproperty

from .base import BaseTeXBotError


class UnknownDjangoError(BaseTeXBotError, RuntimeError):
    """Exception class to raise when an unknown Django error occurs."""

    # noinspection PyMethodParameters,PyPep8Naming
    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:  # noqa: N805
        return "An unknown Django error occurred."
