from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator

from .models import TOWNS


class EventOut(BaseModel):
    id: str
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime | None
    all_day: bool
    venue_name: str | None
    address: str | None
    town: str
    url: str | None
    image_url: str | None
    price_text: str | None

    model_config = {"from_attributes": True}

    @field_serializer("starts_at", "ends_at")
    def _utc_iso(self, v: datetime | None) -> str | None:
        # stored naive-UTC; emit with Z so browsers convert to local correctly
        return None if v is None else v.isoformat() + "Z"


class SourceOut(BaseModel):
    source_id: str
    external_id: str

    model_config = {"from_attributes": True}


class EventDetailOut(EventOut):
    sources: list[SourceOut]


class EventListOut(BaseModel):
    items: list[EventOut]
    total: int
    limit: int
    offset: int


class SubmissionIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    starts_at: datetime
    ends_at: datetime | None = None
    all_day: bool = False
    venue_name: str | None = None
    address: str | None = None
    town: str
    url: str | None = None
    image_url: str | None = None
    price_text: str | None = None
    submitter_email: EmailStr
    # Honeypot — must stay empty (SPEC 6). Deliberately meaningless name:
    # autofill-prone names like "website" get filled by real users' browsers.
    hp_field: str = ""

    @field_validator("town")
    @classmethod
    def town_must_be_known(cls, v: str) -> str:
        if v not in TOWNS:
            raise ValueError(f"town must be one of {TOWNS}")
        return v


class TownCount(BaseModel):
    town: str
    upcoming_events: int


class PendingEventOut(EventOut):
    submitter_email: str | None


class RejectIn(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class ModerationOut(BaseModel):
    id: str
    status: str


class LoginIn(BaseModel):
    password: str


class TipIn(BaseModel):
    message: str = Field(min_length=5, max_length=2000)
    email: EmailStr | None = None


class TipOut(BaseModel):
    id: str
    message: str
    email: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
