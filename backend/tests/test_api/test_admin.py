SUBMISSION = {
    "title": "Community Car Show",
    "starts_at": "2027-06-01T10:00:00",
    "town": "Fairfield",
    "submitter_email": "organizer@example.com",
}


def test_admin_requires_auth(client):
    assert client.get("/api/v1/admin/pending").status_code == 401
    assert client.post("/api/v1/admin/login", json={"password": "wrong"}).status_code == 401


def test_login_then_approve_flow(client):
    event_id = client.post("/api/v1/submissions", json=SUBMISSION).json()["id"]

    assert client.post("/api/v1/admin/login", json={"password": "testpw"}).status_code == 200
    pending = client.get("/api/v1/admin/pending").json()
    assert [e["id"] for e in pending] == [event_id]

    resp = client.post(f"/api/v1/admin/events/{event_id}/approve")
    assert resp.json()["status"] == "approved"
    assert client.get("/api/v1/events").json()["total"] == 1
    assert client.get("/api/v1/admin/pending").json() == []


def test_reject_flow(client):
    event_id = client.post("/api/v1/submissions", json=SUBMISSION).json()["id"]
    headers = {"Authorization": "Bearer testpw"}
    assert client.post(f"/api/v1/admin/events/{event_id}/reject", headers=headers).json()["status"] == "rejected"
    assert client.get("/api/v1/events").json()["total"] == 0
    # can't re-moderate
    assert client.post(f"/api/v1/admin/events/{event_id}/approve", headers=headers).status_code == 404


def test_remove_published_event(client, db):
    from datetime import datetime

    from app.models import Event

    e = Event(title="Spam Concert", town="Stamford", starts_at=datetime(2027, 3, 1), status="approved")
    db.add(e)
    db.commit()
    headers = {"Authorization": "Bearer testpw"}

    assert client.get("/api/v1/events").json()["total"] == 1
    assert client.delete(f"/api/v1/admin/events/{e.id}").status_code == 401  # auth required
    resp = client.delete(f"/api/v1/admin/events/{e.id}", headers=headers)
    assert resp.json()["status"] == "rejected"
    assert client.get("/api/v1/events").json()["total"] == 0
    # removing again -> 404
    assert client.delete(f"/api/v1/admin/events/{e.id}", headers=headers).status_code == 404


def test_removed_event_not_resurrected_by_ingest(client, db):
    from datetime import datetime

    from app.dedup import upsert_event
    from ingest.connectors.base import RawEvent

    raw = RawEvent(external_id="x9", title="Recurring Spam", starts_at=datetime(2027, 3, 1), town="Norwalk")
    event, _ = upsert_event(db, raw, source_id="town-norwalk")
    db.commit()
    headers = {"Authorization": "Bearer testpw"}
    client.delete(f"/api/v1/admin/events/{event.id}", headers=headers)
    db.expire_all()  # the API used its own session; drop our cached copy (prod ingest opens a fresh session)

    # next ingest cycle sees the same feed item again
    event2, action = upsert_event(db, raw, source_id="town-norwalk")
    db.commit()
    assert action == "updated"
    assert event2.id == event.id
    assert event2.status == "rejected"  # stays hidden
    assert client.get("/api/v1/events").json()["total"] == 0
