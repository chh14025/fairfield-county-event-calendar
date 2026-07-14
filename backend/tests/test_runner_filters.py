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


def make_located(title, venue=None, address=None):
    return RawEvent(
        external_id=title, title=title, starts_at=datetime(2026, 8, 1),
        town="Other", venue_name=venue, address=address,
    )


def test_county_filter_keeps_and_tags_local_events():
    from ingest.runner import filter_county_towns

    events = [
        make_located("AI Meetup", venue="Point Café", address="2200 Atlantic St, Stamford, CT"),
        make_located("Berlin Demo Night", venue="Factory Berlin", address="Berlin, Germany"),
        make_located("Online Webinar"),  # no location -> dropped
        make_located("Harbor Talk", venue="SoNo Collection, Norwalk"),
    ]
    kept = filter_county_towns(events)
    assert [(e.title, e.town) for e in kept] == [
        ("AI Meetup", "Stamford"),
        ("Harbor Talk", "Norwalk"),
    ]


def test_prepare_events_combines_filters():
    from ingest.runner import prepare_events

    events = [
        make_located("Library Closed", venue="Stamford Library"),
        make_located("Story Time", venue="Stamford Library"),
        make_located("NYC Gala", venue="Manhattan"),
    ]
    cfg = {"exclude_titles": ["library closed"], "county_towns_only": True}
    assert [e.title for e in prepare_events(events, cfg)] == ["Story Time"]
