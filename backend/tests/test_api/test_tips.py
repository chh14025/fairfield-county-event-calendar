def test_tip_roundtrip(client):
    resp = client.post("/api/v1/tips", json={"message": "Add a map view please!"})
    assert resp.status_code == 201

    assert client.get("/api/v1/admin/tips").status_code == 401  # auth required
    tips = client.get("/api/v1/admin/tips", headers={"Authorization": "Bearer testpw"}).json()
    assert [t["message"] for t in tips] == ["Add a map view please!"]


def test_tip_validation_and_rate_limit(client):
    assert client.post("/api/v1/tips", json={"message": "hi"}).status_code == 422  # too short
    assert client.post("/api/v1/tips", json={"message": "x" * 3000}).status_code == 422  # too long
    for i in range(5):
        assert client.post("/api/v1/tips", json={"message": f"suggestion number {i}"}).status_code == 201
    assert client.post("/api/v1/tips", json={"message": "one too many"}).status_code == 429
