"""Simple value generators to generate random values for environment variables."""

from collections.abc import Sequence

__all__: Sequence[str] = (
    "BaseRandomEnvVariableValueGenerator",
    "RandomDiscordBotTokenGenerator",
    "RandomDiscordLogChannelWebhookURLGenerator",
    "RandomDiscordGuildIDGenerator",
)

import abc
import random
import string
from abc import ABC
from collections.abc import Iterable
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseRandomEnvVariableValueGenerator(Generic[T], ABC):
    """Generates random values for a specific environment variable."""

    @classmethod
    @abc.abstractmethod
    def multiple_values(cls, count: int = 5) -> Iterable[T]:
        """Return `count` number of random values."""

    @classmethod
    def single_value(cls) -> T:
        """Return a single random value."""
        return next(iter(cls.multiple_values(count=1)))


class RandomDiscordBotTokenGenerator(BaseRandomEnvVariableValueGenerator[str]):
    """Generates random values that are valid Discord bot tokens."""

    @classmethod
    def multiple_values(cls, count: int = 5) -> Iterable[str]:
        """Return `count` number of random `DISCORD_BOT_TOKEN` values."""
        return (
            f"{
                "".join(
                    random.choices(
                        string.ascii_letters + string.digits,
                        k=random.randint(24, 26)
                    )
                )
            }.{
                "".join(random.choices(string.ascii_letters + string.digits, k=6))
            }.{
                "".join(
                    random.choices(
                        string.ascii_letters + string.digits + "_-",
                        k=random.randint(27, 38)
                    )
                )
            }"
            for _
            in range(count)
        )

    @classmethod
    def single_value(cls) -> str:
        """Return a single random `DISCORD_BOT_TOKEN` value."""
        return super().single_value()


class RandomDiscordLogChannelWebhookURLGenerator(BaseRandomEnvVariableValueGenerator[str]):
    """Generates random values that are valid Discord log channel webhook URLs."""

    @classmethod
    def multiple_values(cls, count: int = 5, *, with_trailing_slash: bool | None = None) -> Iterable[str]:  # noqa: E501
        """Return `count` number of random `DISCORD_LOG_CHANNEL_WEBHOOK_URL` values."""
        return (
            f"https://discord.com/api/webhooks/{
                "".join(random.choices(string.digits, k=random.randint(17, 20)))
            }/{
                "".join(
                    random.choices(
                        string.ascii_letters + string.digits,
                        k=random.randint(60, 90)
                    )
                )
            }{
                (
                    "/"
                    if with_trailing_slash
                    else (random.choice(("", "/")) if with_trailing_slash is None else "")
                )
            }"
            for _
            in range(count)
        )

    @classmethod
    def single_value(cls) -> str:
        """Return a single random `DISCORD_LOG_CHANNEL_WEBHOOK_URL` value."""
        return super().single_value()


class RandomDiscordGuildIDGenerator(BaseRandomEnvVariableValueGenerator[str]):
    """Generates random values that are valid Discord guild IDs."""

    @classmethod
    def multiple_values(cls, count: int = 5) -> Iterable[str]:
        """Return `count` number of random `DISCORD_GUILD_ID` values."""
        return (
            "".join(random.choices(string.digits, k=random.randint(17, 20)))
            for _
            in range(count)
        )

    @classmethod
    def single_value(cls) -> str:
        """Return a single random `DISCORD_GUILD_ID` value."""
        return super().single_value()