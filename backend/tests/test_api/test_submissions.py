SUBMISSION = {
    "title": "Community Car Show",
    "starts_at": "2027-06-01T10:00:00",
    "town": "Fairfield",
    "submitter_email": "organizer@example.com",
}


def test_submission_creates_pending_event(client):
    resp = client.post("/api/v1/submissions", json=SUBMISSION)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    # not publicly visible yet
    assert client.get("/api/v1/events").json()["total"] == 0


def test_honeypot_silently_drops(client):
    resp = client.post("/api/v1/submissions", json={**SUBMISSION, "hp_field": "spam.biz"})
    assert resp.status_code == 201  # bot sees success...
    assert client.get(
        "/api/v1/admin/pending", headers={"Authorization": "Bearer testpw"}
    ).json() == []  # ...but nothing was stored


def test_unknown_town_rejected(client):
    resp = client.post("/api/v1/submissions", json={**SUBMISSION, "town": "Atlantis"})
    assert resp.status_code == 422


def test_rate_limit(client):
    for _ in range(5):
        assert client.post("/api/v1/submissions", json=SUBMISSION).status_code == 201
    assert client.post("/api/v1/submissions", json=SUBMISSION).status_code == 429
