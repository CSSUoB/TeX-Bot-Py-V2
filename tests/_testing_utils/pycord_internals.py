from collections.abc import Sequence

__all__: Sequence[str] = ("TestingResponse", "TestingInteraction", "TestingApplicationContext")

from collections.abc import Iterable, MutableSequence
from typing import Final

import discord
from discord import Embed, File
from discord.state import ConnectionState
from discord.ui import View

from utils import TeXBotApplicationContext


class TestingResponse:
    def __init__(self, content: str | None = None, *, tts: bool = False, ephemeral: bool = False, file: File | None = None, files: Iterable[File] | None = None, embed: Embed | None = None, embeds: Iterable[Embed] | None = None, view: View | None = None, delete_after: float | None = None) -> None:  # noqa: PLR0913,E501
        if content is not None and not content.strip():
            EMPTY_CONTENT_MESSAGE: Final[str] = f"Parameter {"content"!r} cannot be empty."
            raise ValueError(EMPTY_CONTENT_MESSAGE)

        if file is not None and files is not None:
            INCOMPATIBLE_FILES_PARAMETERS_MESSAGE: Final[str] = (
                f"Parameters {"file"!r} & {"files"!r} cannot both be given."
            )
            raise ValueError(INCOMPATIBLE_FILES_PARAMETERS_MESSAGE)

        if embed is not None and embeds is not None:
            INCOMPATIBLE_EMBEDS_PARAMETERS_MESSAGE: Final[str] = (
                f"Parameters {"embed"!r} & {"embeds"!r} cannot both be given."
            )
            raise ValueError(INCOMPATIBLE_EMBEDS_PARAMETERS_MESSAGE)

        if delete_after is not None and delete_after <= 0:
            INVALID_DELETE_AFTER_MESSAGE: Final[str] = (
                f"Parameter {"delete_after"!r} must be greater than 0."
            )
            raise ValueError(INVALID_DELETE_AFTER_MESSAGE)

        NO_CONTENT_PARAMETERS: Final[bool] = (
            content is None
            and file is None
            and files is None
            and embed is None
            and embeds is None
            and view is None
        )
        if NO_CONTENT_PARAMETERS:
            NO_CONTENT_PARAMETERS_MESSAGE: Final[str] = (
                "Cannot send response with no content parameters given."
            )
            raise ValueError(NO_CONTENT_PARAMETERS_MESSAGE)

        self._content: str | None = content
        self._tts: bool = tts
        self._ephemeral: bool = ephemeral
        self._file: File | None = file
        self._files: Iterable[File] | None = files
        self._embed: Embed | None = embed
        self._embeds: Iterable[Embed] | None = embeds
        self._view: View | None = view
        self._delete_after: float | None = delete_after

    @property
    def content(self) -> str | None:
        return self._content

    @property
    def tts(self) -> bool:
        return self._tts

    @property
    def ephemeral(self) -> bool:
        return self._ephemeral

    @property
    def file(self) -> File | None:
        return self._file

    @property
    def files(self) -> Iterable[File] | None:
        return self._files

    @property
    def embed(self) -> Embed | None:
        return self._embed

    @property
    def embeds(self) -> Iterable[Embed] | None:
        return self._embeds

    @property
    def view(self) -> View | None:
        return self._view

    @property
    def delete_after(self) -> float | None:
        return self._delete_after


class TestingInteraction(discord.Interaction):
    def __init__(self, *, data: discord.types.interactions.Interaction, state: ConnectionState) -> None:  # noqa: E501
        self._responses: MutableSequence[TestingResponse] = []
        super().__init__(data=data, state=state)

    async def respond(self, content: str | None = None, *, username: str | None = None, avatar_url: str | None = None, tts: bool = False, ephemeral: bool = False, file: File | None = None, files: Iterable[File] | None = None, embed: Embed | None = None, embeds: Iterable[Embed] | None = None, view: View | None = None, delete_after: float | None = None) -> discord.Interaction | discord.WebhookMessage:  # noqa: ARG002, PLR0913, E501
        response: TestingResponse = TestingResponse(
            content=content,
            tts=tts,
            ephemeral=ephemeral,
            file=file,
            files=files,
            embed=embed,
            embeds=embeds,
            view=view,
            delete_after=delete_after,
        )

        self._responses.append(response)

        return self

    @property
    def responses(self) -> MutableSequence[TestingResponse]:
        return self._responses


class TestingApplicationContext(TeXBotApplicationContext):
    interaction: TestingInteraction