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
