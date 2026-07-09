PUSH_EVENT = {
    "external_id": "np-1",
    "title": "SoNo Storytime",
    "starts_at": "2027-04-01T14:00:00",
    "town": "Norwalk",
    "venue_name": "SoNo Branch",
}


def test_push_requires_auth(client):
    assert client.post("/api/v1/admin/ingest/lib-norwalk-main", json=[PUSH_EVENT]).status_code == 401


def test_push_upserts_and_dedupes(client):
    headers = {"Authorization": "Bearer testpw"}
    r1 = client.post("/api/v1/admin/ingest/lib-norwalk-main", json=[PUSH_EVENT], headers=headers)
    assert r1.status_code == 200
    assert r1.json() == {"received": 1, "created": 1, "updated": 0, "merged": 0}

    # pushing the same event again updates, not duplicates
    r2 = client.post("/api/v1/admin/ingest/lib-norwalk-main", json=[PUSH_EVENT], headers=headers)
    assert r2.json() == {"received": 1, "created": 0, "updated": 1, "merged": 0}

    events = client.get("/api/v1/events", params={"town": ["Norwalk"]}).json()
    assert events["total"] == 1
    assert events["items"][0]["title"] == "SoNo Storytime"


def test_runner_skips_residential_only():
    from ingest.runner import load_sources

    for cfg in load_sources():
        assert not cfg.get("residential_only"), f"{cfg['id']} should not run server-side"
