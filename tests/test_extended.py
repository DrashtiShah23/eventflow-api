def create_sub(client, headers):
    return client.post('/subscriptions', headers=headers, json={'event_type':'customer.created','target_url':'https://example.com/webhook'}).json()

def create_evt(client, headers):
    return client.post('/events', headers=headers, json={'event_type':'customer.created','source':'crm','payload':{'id':'1'}}).json()

def test_ready(client):
    assert client.get('/ready').json()['status']=='ready'

def test_subscription_controls(client, auth_headers):
    sub=create_sub(client,auth_headers)
    sid=sub['subscription_id']
    assert client.get(f'/subscriptions/{sid}',headers=auth_headers).status_code==200
    assert client.patch(f'/subscriptions/{sid}',headers=auth_headers,json={'active':False}).json()['active'] is False

def test_replay_and_delivery_history(client, auth_headers):
    create_sub(client,auth_headers)
    event=create_evt(client,auth_headers)
    eid=event['event_id']
    replay=client.post(f'/events/{eid}/replay',headers=auth_headers)
    assert replay.status_code==200
    assert len(replay.json())>=1
    history=client.get(f'/events/{eid}/deliveries',headers=auth_headers)
    assert len(history.json())>=1

def test_deadletter_requeue(client, auth_headers):
    sub=create_sub(client,auth_headers)
    event=create_evt(client,auth_headers)
    dlv=client.post(f"/events/{event['event_id']}/replay",headers=auth_headers).json()[0]
    did=dlv['delivery_id']
    for _ in range(3): client.post(f'/deliveries/{did}/retry',headers=auth_headers)
    assert client.get('/deadletters',headers=auth_headers).status_code==200
    rq=client.post(f'/deadletters/{did}/requeue',headers=auth_headers)
    assert rq.status_code==200
    assert rq.json()['status']=='retry_pending'
