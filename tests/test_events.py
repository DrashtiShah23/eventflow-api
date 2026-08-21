def test_create_event(client, auth_headers):
    response = client.post(
        "/events",
        headers=auth_headers,
        json={
            "event_type": "customer.created",
            "source": "crm",
            "payload": {
                "customer_id": "cus_123",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["event_type"] == "customer.created"
    assert body["created"] is True


def test_idempotency(client, auth_headers):
    headers = {
        **auth_headers,
        "Idempotency-Key": "same-request-123",
    }

    payload = {
        "event_type": "payment.completed",
        "source": "billing",
        "payload": {
            "payment_id": "pay_1",
        },
    }

    first = client.post(
        "/events",
        headers=headers,
        json=payload,
    )
    second = client.post(
        "/events",
        headers=headers,
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["event_id"] == second.json()["event_id"]
    assert first.json()["created"] is True
    assert second.json()["created"] is False


def test_event_filtering(client, auth_headers):
    client.post(
        "/events",
        headers=auth_headers,
        json={
            "event_type": "device.failed",
            "source": "router",
            "payload": {
                "device_id": "r1",
            },
        },
    )

    response = client.get(
        "/events?event_type=device.failed",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
