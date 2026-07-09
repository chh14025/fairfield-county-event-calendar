"""Deduplication engine (SPEC 5)."""
import logging
from datetime import timedelta

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from ingest.connectors.base import RawEvent

from .models import Event, EventSource
from .utils import utcnow

log = logging.getLogger("dedup")

FUZZY_THRESHOLD = 85
REVIEW_THRESHOLD = 70
TIME_WINDOW = timedelta(minutes=30)


def title_similarity(a: str, b: str) -> float:
    return fuzz.token_set_ratio(a.lower().strip(), b.lower().strip())


def find_duplicate(db: Session, raw: RawEvent) -> Event | None:
    candidates = (
        db.query(Event)
        .filter(
            Event.town == raw.town,
            Event.starts_at >= raw.starts_at - TIME_WINDOW,
            Event.starts_at <= raw.starts_at + TIME_WINDOW,
        )
        .all()
    )
    best, best_score = None, 0.0
    for c in candidates:
        score = title_similarity(raw.title, c.title)
        if score > best_score:
            best, best_score = c, score
    if best is not None and best_score >= FUZZY_THRESHOLD:
        return best
    if best is not None and best_score >= REVIEW_THRESHOLD:
        # v1: log only; dedup review UI is v1.1 (SPEC 5.4)
        log.warning("Ambiguous dedup (%.0f): %r vs %r", best_score, raw.title, best.title)
    return None


def _is_authoritative(source_id: str) -> bool:
    """Town-government feeds win on time/venue (SPEC 5.3)."""
    return source_id.startswith("town-")


def _merge_fields(event: Event, raw: RawEvent, source_id: str) -> None:
    if raw.description and len(raw.description) > len(event.description or ""):
        event.description = raw.description
    if _is_authoritative(source_id):
        event.starts_at = raw.starts_at
        event.ends_at = raw.ends_at
        if raw.venue_name:
            event.venue_name = raw.venue_name
    else:
        event.venue_name = event.venue_name or raw.venue_name
    event.address = event.address or raw.address
    event.url = event.url or raw.url  # earliest-seen keeps canonical URL
    event.image_url = event.image_url or raw.image_url
    event.price_text = event.price_text or raw.price_text


def upsert_event(db: Session, raw: RawEvent, source_id: str) -> tuple[Event, str]:
    """Returns (event, action) where action is 'created' | 'updated' | 'merged'."""
    existing_src = (
        db.query(EventSource)
        .filter_by(source_id=source_id, external_id=raw.external_id)
        .one_or_none()
    )
    if existing_src is not None:
        event = existing_src.event
        _merge_fields(event, raw, source_id)
        event.title = raw.title
        existing_src.last_seen_at = utcnow()
        existing_src.raw = raw.model_dump(mode="json")
        db.flush()
        return event, "updated"

    dup = find_duplicate(db, raw)
    if dup is not None:
        _merge_fields(dup, raw, source_id)
        db.add(
            EventSource(
                event_id=dup.id,
                source_id=source_id,
                external_id=raw.external_id,
                raw=raw.model_dump(mode="json"),
            )
        )
        db.flush()
        return dup, "merged"

    event = Event(
        title=raw.title,
        description=raw.description,
        starts_at=raw.starts_at,
        ends_at=raw.ends_at,
        all_day=raw.all_day,
        venue_name=raw.venue_name,
        address=raw.address,
        town=raw.town,
        url=raw.url,
        image_url=raw.image_url,
        price_text=raw.price_text,
        status="approved",  # ingested events auto-approve (SPEC 4)
    )
    db.add(event)
    db.flush()
    db.add(
        EventSource(
            event_id=event.id,
            source_id=source_id,
            external_id=raw.external_id,
            raw=raw.model_dump(mode="json"),
        )
    )
    db.flush()
    return event, "created"
