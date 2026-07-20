from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Protocol


@dataclass(frozen=True)
class RawRecord:
    source_name: str
    source_type: str
    source_url: str
    collected_at: datetime
    payload: dict[str, Any]


@dataclass(frozen=True)
class SourceFetchStatus:
    source_name: str
    source_type: str
    status: str
    record_count: int
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    error_type: str | None = None
    error_message: str | None = None


class SourceConnector(Protocol):
    source_name: str
    source_type: str

    def fetch(self) -> list[RawRecord]:
        """Return raw records from one source."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def fetch_with_status(
    source: SourceConnector,
    handled_errors: tuple[type[Exception], ...],
) -> tuple[list[RawRecord], SourceFetchStatus]:
    started_at = utc_now()
    timer = perf_counter()
    try:
        records = source.fetch()
    except handled_errors as error:
        completed_at = utc_now()
        return [], SourceFetchStatus(
            source_name=source.source_name,
            source_type=source.source_type,
            status="failed",
            record_count=0,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=round((perf_counter() - timer) * 1000),
            error_type=type(error).__name__,
            error_message=str(error)[:500],
        )

    completed_at = utc_now()
    return records, SourceFetchStatus(
        source_name=source.source_name,
        source_type=source.source_type,
        status="success" if records else "empty",
        record_count=len(records),
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=round((perf_counter() - timer) * 1000),
    )
