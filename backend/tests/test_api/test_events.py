from datetime import datetime, timedelta

from app.models import Event

FUTURE = datetime(2027, 1, 15, 18, 0)


def seed(db):
    db.add_all(
        [
            Event(title="Jazz Night", town="Stamford", starts_at=FUTURE, status="approved", price_text="Free"),
            Event(title="Winter Market", town="Westport", starts_at=FUTURE + timedelta(days=1), status="approved", price_text="$5"),
            Event(title="Pending Thing", town="Stamford", starts_at=FUTURE, status="pending"),
            Event(title="Old Gala", town="Stamford", starts_at=datetime(2020, 1, 1), status="expired"),
        ]
    )
    db.commit()


def test_lists_only_approved_upcoming(client, db):
    seed(db)
    data = client.get("/api/v1/events").json()
    titles = [e["title"] for e in data["items"]]
    assert titles == ["Jazz Night", "Winter Market"]
    assert data["total"] == 2


def test_town_filter(client, db):
    seed(db)
    data = client.get("/api/v1/events", params={"town": ["Westport"]}).json()
    assert [e["title"] for e in data["items"]] == ["Winter Market"]


def test_text_search_and_free_only(client, db):
    seed(db)
    assert client.get("/api/v1/events", params={"q": "jazz"}).json()["total"] == 1
    assert client.get("/api/v1/events", params={"free_only": True}).json()["total"] == 1


def test_detail_hides_pending(client, db):
    seed(db)
    pending_id = db.query(Event).filter_by(title="Pending Thing").one().id
    approved_id = db.query(Event).filter_by(title="Jazz Night").one().id
    assert client.get(f"/api/v1/events/{pending_id}").status_code == 404
    body = client.get(f"/api/v1/events/{approved_id}").json()
    assert body["title"] == "Jazz Night"
    assert "sources" in body


def test_ics_feed(client, db):
    seed(db)
    resp = client.get("/api/v1/events.ics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/calendar")
    assert b"Jazz Night" in resp.content


def test_towns_counts(client, db):
    seed(db)
    towns = {t["town"]: t["upcoming_events"] for t in client.get("/api/v1/towns").json()}
    assert towns["Stamford"] == 1
    assert towns["Westport"] == 1
    assert towns["Danbury"] == 0


def test_per_event_ics_download(client, db):
    seed(db)
    event = db.query(Event).filter_by(title="Jazz Night").one()
    resp = client.get(f"/api/v1/events/{event.id}.ics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/calendar")
    assert b"Jazz Night" in resp.content
    assert b"DTSTART:20270115T180000Z" in resp.content  # explicit UTC, not floating

    pending = db.query(Event).filter_by(title="Pending Thing").one()
    assert client.get(f"/api/v1/events/{pending.id}.ics").status_code == 404


def test_event_datetimes_serialized_as_utc(client, db):
    seed(db)
    item = client.get("/api/v1/events").json()["items"][0]
    assert item["starts_at"].endswith("Z")
