from datetime import datetime
from pathlib import Path

from ingest.connectors.ical_feed import parse_ical

FIXTURE = Path(__file__).parent.parent / "fixtures" / "town_sample.ics"


def test_parses_timed_event():
    events = parse_ical(FIXTURE.read_bytes(), town="Westport")
    market = next(e for e in events if e.external_id == "evt-1001@westportct.gov")
    assert market.title == "Westport Farmers Market"
    assert market.starts_at == datetime(2026, 7, 16, 14, 0)
    assert market.ends_at == datetime(2026, 7, 16, 18, 0)
    assert market.venue_name == "Imperial Avenue Parking Lot"
    assert market.town == "Westport"
    assert market.url == "https://westportct.gov/events/1001"
    assert market.all_day is False


def test_parses_all_day_event():
    events = parse_ical(FIXTURE.read_bytes(), town="Westport")
    fireworks = next(e for e in events if e.external_id == "evt-1002@westportct.gov")
    assert fireworks.all_day is True
    assert fireworks.starts_at == datetime(2026, 7, 4)


def test_skips_events_missing_required_fields():
    broken = b"BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nUID:x\nEND:VEVENT\nEND:VCALENDAR\n"
    assert parse_ical(broken, town="Westport") == []


def test_skips_season_long_allday_placeholders():
    """The Events Calendar exports series as one months-long all-day event; drop those."""
    ics = (
        b"BEGIN:VCALENDAR\nVERSION:2.0\n"
        b"BEGIN:VEVENT\nUID:season-1\nSUMMARY:Farmers Market (Season)\n"
        b"DTSTART;VALUE=DATE:20260613\nDTEND;VALUE=DATE:20261011\nEND:VEVENT\n"
        b"BEGIN:VEVENT\nUID:occ-1\nSUMMARY:Farmers Market\n"
        b"DTSTART:20260711T130000Z\nDTEND:20260711T170000Z\nEND:VEVENT\n"
        b"BEGIN:VEVENT\nUID:fest-1\nSUMMARY:Weekend Festival\n"
        b"DTSTART;VALUE=DATE:20260711\nDTEND;VALUE=DATE:20260713\nEND:VEVENT\n"
        b"END:VCALENDAR\n"
    )
    ids = {e.external_id for e in parse_ical(ics, town="Stamford")}
    assert ids == {"occ-1", "fest-1"}  # season placeholder dropped, short span kept


def test_relative_url_falls_back_to_feed_url():
    """CivicPlus feeds put relative paths in URL; fall back to the feed URL."""
    ics = (
        b"BEGIN:VCALENDAR\nVERSION:2.0\n"
        b"BEGIN:VEVENT\nUID:cp-1\nSUMMARY:Summer Concert\n"
        b"DTSTART:20260722T230000Z\n"
        b"URL:/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID=32\n"
        b"END:VEVENT\nEND:VCALENDAR\n"
    )
    (event,) = parse_ical(ics, town="Greenwich", base_url="https://example.gov/feed")
    assert event.url == "https://example.gov/feed"


def test_strips_html_from_text_fields():
    """CivicPlus feeds embed styled HTML in LOCATION/DESCRIPTION."""
    ics = (
        b"BEGIN:VCALENDAR\nVERSION:2.0\n"
        b"BEGIN:VEVENT\nUID:html-1\nSUMMARY:Pilates [ZOOM] with Wendy\n"
        b"DTSTART:20260722T191500Z\n"
        b'DESCRIPTION:<p><span style="color: rgb(51\\,51\\,51)\\; font-family: Arial">'
        b"This class is via ZOOM</span></p>\n"
        b"LOCATION:<p>Binney Park</p> -   Greenwich CT 06830\n"
        b"END:VEVENT\nEND:VCALENDAR\n"
    )
    (event,) = parse_ical(ics, town="Greenwich")
    assert event.description == "This class is via ZOOM"
    assert event.venue_name == "Binney Park - Greenwich CT 06830"
    assert "<" not in event.title
