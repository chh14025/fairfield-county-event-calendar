from datetime import datetime, timedelta

from app.dedup import upsert_event
from ingest.connectors.base import RawEvent

START = datetime(2026, 8, 1, 18, 0)


def raw(**kw) -> RawEvent:
    base = dict(external_id="x1", title="Norwalk Car Show", starts_at=START, town="Norwalk")
    base.update(kw)
    return RawEvent(**base)


def test_same_source_same_external_id_updates(db):
    e1, a1 = upsert_event(db, raw(), source_id="town-norwalk")
    e2, a2 = upsert_event(db, raw(description="Updated desc"), source_id="town-norwalk")
    assert (a1, a2) == ("created", "updated")
    assert e1.id == e2.id
    assert e2.description == "Updated desc"


def test_cross_source_fuzzy_match_merges(db):
    e1, _ = upsert_event(db, raw(), source_id="town-norwalk")
    e2, action = upsert_event(
        db,
        raw(external_id="ct-99", title="Car Show — Norwalk", starts_at=START + timedelta(minutes=15)),
        source_id="ctvisit",
    )
    assert action == "merged"
    assert e2.id == e1.id
    assert {s.source_id for s in e1.sources} == {"town-norwalk", "ctvisit"}


def test_different_events_not_merged(db):
    e1, _ = upsert_event(db, raw(), source_id="town-norwalk")
    e2, action = upsert_event(
        db,
        raw(external_id="lib-1", title="Toddler Story Time", starts_at=START),
        source_id="libcal-norwalk",
    )
    assert action == "created"
    assert e2.id != e1.id


def test_different_time_not_merged(db):
    e1, _ = upsert_event(db, raw(), source_id="town-norwalk")
    e2, action = upsert_event(
        db,
        raw(external_id="ct-99", starts_at=START + timedelta(hours=3)),
        source_id="ctvisit",
    )
    assert action == "created"
    assert e2.id != e1.id


def test_town_source_wins_time_and_venue(db):
    upsert_event(db, raw(external_id="ct-99", venue_name="Somewhere"), source_id="ctvisit")
    e, action = upsert_event(
        db,
        raw(starts_at=START + timedelta(minutes=10), venue_name="Veterans Park"),
        source_id="town-norwalk",
    )
    assert action == "merged"
    assert e.starts_at == START + timedelta(minutes=10)
    assert e.venue_name == "Veterans Park"
