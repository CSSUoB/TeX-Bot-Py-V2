"""Module for generating random values for environment variables."""

import abc
import random
import string
from collections.abc import Iterable
from typing import TYPE_CHECKING, Generic, TypeVar, override

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


__all__: "Sequence[str]" = (
    "BaseRandomEnvVariableValueGenerator",
    "RandomDiscordBotTokenGenerator",
    "RandomDiscordGuildIDGenerator",
    "RandomDiscordLogChannelWebhookURLGenerator",
    "RandomOrganisationIDGenerator",
)


T = TypeVar("T")


class BaseRandomEnvVariableValueGenerator(Generic[T], abc.ABC):
    """Generates random values for a specific environment variable."""

    @classmethod
    @abc.abstractmethod
    def multiple_values(cls, count: int = 5) -> "Iterable[T]":
        """Return `count` number of random values."""

    @classmethod
    def single_value(cls) -> T:
        """Return a single random value."""
        return next(iter(cls.multiple_values(count=1)))


class RandomDiscordBotTokenGenerator(BaseRandomEnvVariableValueGenerator[str]):
    """Generates random values that are valid Discord bot tokens."""

    @classmethod
    @override
    def multiple_values(cls, count: int = 5) -> "Iterable[str]":
        """Return `count` number of random `DISCORD_BOT_TOKEN` values."""
        return (
            f"{
                ''.join(
                    random.choices(
                        string.ascii_letters + string.digits, k=random.randint(24, 26)
                    )
                )
            }.{''.join(random.choices(string.ascii_letters + string.digits, k=6))}.{
                ''.join(
                    random.choices(
                        string.ascii_letters + string.digits + '_-', k=random.randint(27, 38)
                    )
                )
            }"  # noqa: S311
            for _ in range(count)
        )

    @classmethod
    @override
    def single_value(cls) -> str:
        """Return a single random `DISCORD_BOT_TOKEN` value."""
        return super().single_value()


class RandomDiscordLogChannelWebhookURLGenerator(BaseRandomEnvVariableValueGenerator[str]):
    """Generates random values that are valid Discord log channel webhook URLs."""

    @classmethod
    @override
    def multiple_values(
        cls, count: int = 5, *, with_trailing_slash: bool | None = None
    ) -> "Iterable[str]":
        """Return `count` number of random `DISCORD_LOG_CHANNEL_WEBHOOK_URL` values."""
        return (
            f"https://discord.com/api/webhooks/{
                ''.join(random.choices(string.digits, k=random.randint(17, 20)))
            }/{
                ''.join(
                    random.choices(
                        string.ascii_letters + string.digits, k=random.randint(60, 90)
                    )
                )
            }{
                (
                    '/'
                    if with_trailing_slash
                    else (random.choice(('', '/')) if with_trailing_slash is None else '')
                )
            }"  # noqa: S311
            for _ in range(count)
        )

    @classmethod
    @override
    def single_value(cls) -> str:
        """Return a single random `DISCORD_LOG_CHANNEL_WEBHOOK_URL` value."""
        return super().single_value()


class RandomDiscordGuildIDGenerator(BaseRandomEnvVariableValueGenerator[str]):
    """Generates random values that are valid Discord guild IDs."""

    @classmethod
    @override
    def multiple_values(cls, count: int = 5) -> "Iterable[str]":
        """Return `count` number of random `DISCORD_GUILD_ID` values."""
        return (
            "".join(random.choices(string.digits, k=random.randint(17, 20)))  # noqa: S311
            for _ in range(count)
        )

    @classmethod
    @override
    def single_value(cls) -> str:
        """Return a single random `DISCORD_GUILD_ID` value."""
        return super().single_value()


class RandomOrganisationIDGenerator(BaseRandomEnvVariableValueGenerator[str]):
    """Generates random values that are valid organisation IDs."""

    @classmethod
    @override
    def multiple_values(cls, count: int = 5) -> "Iterable[str]":
        """Return `count` number of random `ORGANISATION_ID` values."""
        return (
            "".join(random.choices(string.digits, k=random.randint(4, 5)))  # noqa: S311
            for _ in range(count)
        )

    @classmethod
    @override
    def single_value(cls) -> str:
        """Return a single random `ORGANISATION_ID` value."""
        return super().single_value()
