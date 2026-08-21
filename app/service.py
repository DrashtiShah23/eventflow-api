import json
import uuid
from datetime import datetime, timezone
import requests
from sqlalchemy.orm import Session
from app.models import Delivery, Event, Subscription

MAX_DELIVERY_ATTEMPTS = 3

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def serialize_event(event):
    return {"event_id": event.event_id, "event_type": event.event_type, "source": event.source, "payload": json.loads(event.payload_json), "status": event.status, "created_at": event.created_at.isoformat(), "processed_at": event.processed_at.isoformat() if event.processed_at else None}

def serialize_subscription(subscription):
    return {"subscription_id": subscription.subscription_id, "event_type": subscription.event_type, "target_url": subscription.target_url, "active": subscription.active, "created_at": subscription.created_at.isoformat()}

def serialize_delivery(delivery):
    return {"delivery_id": delivery.delivery_id, "event_id": delivery.event_id, "subscription_id": delivery.subscription_id, "attempt_count": delivery.attempt_count, "status": delivery.status, "last_error": delivery.last_error, "created_at": delivery.created_at.isoformat(), "updated_at": delivery.updated_at.isoformat()}

def create_event(db, event_type, source, payload, idempotency_key):
    if idempotency_key:
        existing = db.query(Event).filter(Event.idempotency_key == idempotency_key).first()
        if existing:
            return existing, False
    event = Event(event_id=f"evt_{uuid.uuid4().hex}", idempotency_key=idempotency_key, event_type=event_type, source=source, payload_json=json.dumps(payload), status="pending", created_at=utcnow(), processed_at=None)
    db.add(event); db.commit(); db.refresh(event)
    return event, True

def create_subscription(db, event_type, target_url):
    sub = Subscription(subscription_id=f"sub_{uuid.uuid4().hex}", event_type=event_type, target_url=target_url, active=True, created_at=utcnow())
    db.add(sub); db.commit(); db.refresh(sub)
    return sub

def process_event(db, event_id):
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event: return None
    subs = db.query(Subscription).filter(Subscription.active.is_(True), Subscription.event_type == event.event_type).all()
    for sub in subs:
        db.add(Delivery(delivery_id=f"dlv_{uuid.uuid4().hex}", event_id=event.event_id, subscription_id=sub.subscription_id, attempt_count=0, status="pending", last_error=None, created_at=utcnow(), updated_at=utcnow()))
    event.status = "processed"; event.processed_at = utcnow(); db.commit(); db.refresh(event)
    return event

def replay_event(db, event):
    subs = db.query(Subscription).filter(Subscription.active.is_(True), Subscription.event_type == event.event_type).all()
    created = []
    for sub in subs:
        d = Delivery(delivery_id=f"dlv_{uuid.uuid4().hex}", event_id=event.event_id, subscription_id=sub.subscription_id, attempt_count=0, status="pending", last_error=None, created_at=utcnow(), updated_at=utcnow())
        db.add(d); created.append(d)
    db.commit()
    for d in created: db.refresh(d)
    return created

def attempt_delivery(db, delivery, timeout_seconds=5.0):
    sub = db.query(Subscription).filter(Subscription.subscription_id == delivery.subscription_id).first()
    event = db.query(Event).filter(Event.event_id == delivery.event_id).first()
    if not sub or not event:
        delivery.status = "dead_letter"; delivery.last_error = "Related subscription or event was not found."; delivery.updated_at = utcnow(); db.commit(); return delivery
    delivery.attempt_count += 1
    try:
        response = requests.post(sub.target_url, json=serialize_event(event), timeout=timeout_seconds)
        response.raise_for_status(); delivery.status = "delivered"; delivery.last_error = None
    except requests.RequestException as exc:
        delivery.last_error = str(exc); delivery.status = "dead_letter" if delivery.attempt_count >= MAX_DELIVERY_ATTEMPTS else "retry_pending"
    delivery.updated_at = utcnow(); db.commit(); db.refresh(delivery); return delivery

def retry_pending_deliveries(db):
    return [attempt_delivery(db, d) for d in db.query(Delivery).filter(Delivery.status.in_(["pending", "retry_pending"])).all()]

def requeue_dead_letter(db, delivery):
    delivery.status = "retry_pending"; delivery.attempt_count = 0; delivery.last_error = None; delivery.updated_at = utcnow(); db.commit(); db.refresh(delivery); return delivery
