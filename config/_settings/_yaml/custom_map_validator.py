from collections.abc import Sequence

__all__: Sequence[str] = ("SlugKeyValidator", "SlugKeyMap")


from typing import override

import slugify
import strictyaml
from strictyaml.yamllocation import YAMLChunk


class SlugKeyValidator(strictyaml.ScalarValidator):  # type: ignore[misc]
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> str:  # type: ignore[misc]
        return slugify.slugify(str(chunk.contents))


class SlugKeyMap(strictyaml.Map):  # type: ignore[misc]
    @override
    def __init__(self, validator: dict[object, object], key_validator: strictyaml.Validator | None = None) -> None:  # type: ignore[misc] # noqa: E501
        super().__init__(
            validator=validator,
            key_validator=key_validator if key_validator is not None else SlugKeyValidator(),
        )
