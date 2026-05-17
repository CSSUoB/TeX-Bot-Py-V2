from typing import override

from .yamllocation import YAMLChunk

class YAML: ...

class Validator:
    def should_be_string(self, data: object, message: str) -> None: ...
    def to_yaml(self, data: object) -> object: ...

class MapValidator(Validator):
    _validator_dict: dict[str, Validator]

class ScalarValidator(Validator):
    def validate_scalar(self, chunk: YAMLChunk) -> object: ...

class Map(MapValidator):
    def __init__(self, validator_dict: dict[object, object], key_validator: Validator | None = ...) -> None: ...

class Float(ScalarValidator):
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> float: ...

class Int(ScalarValidator):
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> int: ...

class Bool(ScalarValidator):
    @override
    def validate_scalar(self, chunk: YAMLChunk) -> bool: ...


class Url(ScalarValidator):
    def __is_absolute_url(self, raw: str) -> bool: ...


