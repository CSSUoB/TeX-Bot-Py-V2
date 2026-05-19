"""Custom exception classes raised when errors occur during use of MSL features."""

from typing import TYPE_CHECKING, override

from typed_classproperties import classproperty

from .base import BaseTeXBotError

if TYPE_CHECKING:
    from collections.abc import Sequence


__all__: Sequence[str] = ("MSLMembershipError",)


class MSLMembershipError(BaseTeXBotError, RuntimeError):
    """
    Exception class to raise when any error occurs while checking MSL membership.

    If this error occurs, it is likely that MSL features will not work correctly.
    """

    @classproperty
    @override
    def DEFAULT_MESSAGE(cls) -> str:
        return "An error occurred while trying to fetch membership data from MSL."
