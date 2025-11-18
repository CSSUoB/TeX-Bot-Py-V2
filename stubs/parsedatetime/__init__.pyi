import datetime
import time
from collections.abc import Sequence
from zoneinfo import ZoneInfo

__all__: Sequence[str] = ("Calendar",)

class Calendar:
    def parseDT(
        self,
        dateString: str,
        sourceTime: (
            time.struct_time | datetime.datetime | datetime.date | datetime.time | None
        ) = ...,
        tzinfo: ZoneInfo | None = ...,
        version: int | None = ...,
    ) -> tuple[time.struct_time, int]: ...
