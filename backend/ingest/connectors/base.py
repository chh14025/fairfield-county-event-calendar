"""Connector interface (SPEC 3). Every source implements fetch() -> list[RawEvent]."""
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel


class RawEvent(BaseModel):
    external_id: str
    title: str
    description: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    all_day: bool = False
    venue_name: str | None = None
    address: str | None = None
    town: str = "Other"
    url: str | None = None
    image_url: str | None = None
    price_text: str | None = None


class Connector(Protocol):
    source_id: str

    def fetch(self) -> list[RawEvent]: ...


USER_AGENT = "FairfieldCountyEvents/0.1 (+community event aggregator)"
