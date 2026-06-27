from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(frozen=True)
class RawRecord:
    source_name: str
    source_type: str
    source_url: str
    collected_at: datetime
    payload: dict[str, Any]


class SourceConnector(Protocol):
    source_name: str
    source_type: str

    def fetch(self) -> list[RawRecord]:
        """Return raw records from one source."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
