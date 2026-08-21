def test_metrics(client, auth_headers):
    client.post(
        "/events",
        headers=auth_headers,
        json={
            "event_type": "job.completed",
            "source": "worker",
            "payload": {
                "job_id": "job_1",
            },
        },
    )

    response = client.get(
        "/metrics",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["events_total"] == 1
