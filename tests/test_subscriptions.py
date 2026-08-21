def test_create_subscription(client, auth_headers):
    response = client.post(
        "/subscriptions",
        headers=auth_headers,
        json={
            "event_type": "customer.created",
            "target_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == 200
    assert response.json()["event_type"] == "customer.created"
    assert response.json()["active"] is True
