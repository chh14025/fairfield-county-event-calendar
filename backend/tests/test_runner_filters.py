from datetime import datetime

from ingest.connectors.base import RawEvent
from ingest.runner import filter_events


def make(title):
    return RawEvent(external_id=title, title=title, starts_at=datetime(2026, 8, 1), town="Greenwich")


def test_filter_events_drops_excluded_titles_case_insensitive():
    events = [make("Byram Shubert LIBRARY CLOSED"), make("Storytime"), make("Book Club")]
    kept = filter_events(events, ["library closed"])
    assert [e.title for e in kept] == ["Storytime", "Book Club"]


def test_filter_events_noop_without_patterns():
    events = [make("Library Closed")]
    assert filter_events(events, []) == events
