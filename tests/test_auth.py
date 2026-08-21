def test_protected_route_requires_api_key(client):
    response = client.get("/events")

    assert response.status_code == 401
