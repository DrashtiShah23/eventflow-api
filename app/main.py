from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.models import Delivery, Event, Subscription
from app.schemas import EventCreate, SubscriptionCreate, SubscriptionUpdate
from app.security import require_api_key
from app.service import *

Base.metadata.create_all(bind=engine)
app = FastAPI(title="EventFlow API Platform", version="2.0.0")

def not_found(name):
    raise HTTPException(status_code=404, detail=f"{name} not found.")

@app.get("/health")
def health(): return {"status":"ok","service":"eventflow"}

@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(__import__('sqlalchemy').text("SELECT 1"))
    return {"status":"ready","database":"ok"}

@app.get("/metrics", dependencies=[Depends(require_api_key)])
def metrics(db: Session = Depends(get_db)):
    return {
        "events_total": db.query(func.count(Event.id)).scalar() or 0,
        "events_pending": db.query(func.count(Event.id)).filter(Event.status=="pending").scalar() or 0,
        "subscriptions_active": db.query(func.count(Subscription.id)).filter(Subscription.active.is_(True)).scalar() or 0,
        "deliveries_pending": db.query(func.count(Delivery.id)).filter(Delivery.status.in_(["pending","retry_pending"])).scalar() or 0,
        "deliveries_delivered": db.query(func.count(Delivery.id)).filter(Delivery.status=="delivered").scalar() or 0,
        "deliveries_dead_letter": db.query(func.count(Delivery.id)).filter(Delivery.status=="dead_letter").scalar() or 0,
    }

@app.post("/events", dependencies=[Depends(require_api_key)])
def ingest_event(body: EventCreate, background_tasks: BackgroundTasks, idempotency_key: str|None = Header(default=None, alias="Idempotency-Key"), db: Session=Depends(get_db)):
    event, created = create_event(db, body.event_type, body.source, body.payload, idempotency_key)
    if created: background_tasks.add_task(_process_event_task, event.event_id)
    out = serialize_event(event); out["created"] = created; return out

def _process_event_task(event_id: str):
    from app.database import SessionLocal
    db=SessionLocal()
    try: process_event(db,event_id)
    finally: db.close()

@app.get("/events", dependencies=[Depends(require_api_key)])
def list_events(event_type:str|None=None, source:str|None=None, status:str|None=None, limit:int=50, offset:int=0, db:Session=Depends(get_db)):
    q=db.query(Event)
    if event_type: q=q.filter(Event.event_type==event_type)
    if source: q=q.filter(Event.source==source)
    if status: q=q.filter(Event.status==status)
    return [serialize_event(x) for x in q.order_by(Event.id.desc()).offset(offset).limit(min(limit,100)).all()]

@app.get("/events/{event_id}", dependencies=[Depends(require_api_key)])
def get_event(event_id:str, db:Session=Depends(get_db)):
    e=db.query(Event).filter(Event.event_id==event_id).first()
    if not e: not_found("Event")
    return serialize_event(e)

@app.get("/events/{event_id}/deliveries", dependencies=[Depends(require_api_key)])
def event_deliveries(event_id:str, db:Session=Depends(get_db)):
    if not db.query(Event).filter(Event.event_id==event_id).first(): not_found("Event")
    return [serialize_delivery(x) for x in db.query(Delivery).filter(Delivery.event_id==event_id).order_by(Delivery.id.desc()).all()]

@app.post("/events/{event_id}/replay", dependencies=[Depends(require_api_key)])
def replay(event_id:str, db:Session=Depends(get_db)):
    e=db.query(Event).filter(Event.event_id==event_id).first()
    if not e: not_found("Event")
    return [serialize_delivery(x) for x in replay_event(db,e)]

@app.post("/subscriptions", dependencies=[Depends(require_api_key)])
def add_subscription(body:SubscriptionCreate, db:Session=Depends(get_db)):
    return serialize_subscription(create_subscription(db, body.event_type, str(body.target_url)))

@app.get("/subscriptions", dependencies=[Depends(require_api_key)])
def list_subscriptions(event_type:str|None=None, active:bool|None=None, db:Session=Depends(get_db)):
    q=db.query(Subscription)
    if event_type: q=q.filter(Subscription.event_type==event_type)
    if active is not None: q=q.filter(Subscription.active.is_(active))
    return [serialize_subscription(x) for x in q.order_by(Subscription.id.desc()).all()]

@app.get("/subscriptions/{subscription_id}", dependencies=[Depends(require_api_key)])
def get_subscription(subscription_id:str, db:Session=Depends(get_db)):
    s=db.query(Subscription).filter(Subscription.subscription_id==subscription_id).first()
    if not s: not_found("Subscription")
    out=serialize_subscription(s); out["delivery_count"] = db.query(func.count(Delivery.id)).filter(Delivery.subscription_id==subscription_id).scalar() or 0; return out

@app.patch("/subscriptions/{subscription_id}", dependencies=[Depends(require_api_key)])
def patch_subscription(subscription_id:str, body:SubscriptionUpdate, db:Session=Depends(get_db)):
    s=db.query(Subscription).filter(Subscription.subscription_id==subscription_id).first()
    if not s: not_found("Subscription")
    s.active=body.active; db.commit(); db.refresh(s); return serialize_subscription(s)

@app.delete("/subscriptions/{subscription_id}", dependencies=[Depends(require_api_key)])
def delete_subscription(subscription_id:str, db:Session=Depends(get_db)):
    s=db.query(Subscription).filter(Subscription.subscription_id==subscription_id).first()
    if not s: not_found("Subscription")
    s.active=False; db.commit(); return {"deleted":True,"subscription_id":subscription_id}

@app.post("/subscriptions/{subscription_id}/test", dependencies=[Depends(require_api_key)])
def test_subscription(subscription_id:str, db:Session=Depends(get_db)):
    s=db.query(Subscription).filter(Subscription.subscription_id==subscription_id).first()
    if not s: not_found("Subscription")
    e,_=create_event(db,"eventflow.test","eventflow",{"subscription_id":subscription_id},None)
    d=Delivery(delivery_id=f"dlv_{__import__('uuid').uuid4().hex}", event_id=e.event_id, subscription_id=s.subscription_id, attempt_count=0, status="pending", last_error=None, created_at=utcnow(), updated_at=utcnow()); db.add(d); db.commit(); db.refresh(d)
    return serialize_delivery(d)

@app.get("/deliveries", dependencies=[Depends(require_api_key)])
def list_deliveries(status:str|None=None, event_id:str|None=None, subscription_id:str|None=None, limit:int=50, db:Session=Depends(get_db)):
    q=db.query(Delivery)
    if status: q=q.filter(Delivery.status==status)
    if event_id: q=q.filter(Delivery.event_id==event_id)
    if subscription_id: q=q.filter(Delivery.subscription_id==subscription_id)
    return [serialize_delivery(x) for x in q.order_by(Delivery.id.desc()).limit(min(limit,100)).all()]

@app.get("/deliveries/{delivery_id}", dependencies=[Depends(require_api_key)])
def get_delivery(delivery_id:str, db:Session=Depends(get_db)):
    d=db.query(Delivery).filter(Delivery.delivery_id==delivery_id).first()
    if not d: not_found("Delivery")
    return serialize_delivery(d)

@app.post("/deliveries/{delivery_id}/retry", dependencies=[Depends(require_api_key)])
def retry_delivery(delivery_id:str, db:Session=Depends(get_db)):
    d=db.query(Delivery).filter(Delivery.delivery_id==delivery_id).first()
    if not d: not_found("Delivery")
    return serialize_delivery(attempt_delivery(db,d,timeout_seconds=0.25))

@app.post("/deliveries/retry", dependencies=[Depends(require_api_key)])
def retry_deliveries(db:Session=Depends(get_db)):
    return [serialize_delivery(x) for x in retry_pending_deliveries(db)]

@app.get("/deadletters", dependencies=[Depends(require_api_key)])
def deadletters(db:Session=Depends(get_db)):
    return [serialize_delivery(x) for x in db.query(Delivery).filter(Delivery.status=="dead_letter").order_by(Delivery.id.desc()).all()]

@app.post("/deadletters/{delivery_id}/requeue", dependencies=[Depends(require_api_key)])
def requeue(delivery_id:str, db:Session=Depends(get_db)):
    d=db.query(Delivery).filter(Delivery.delivery_id==delivery_id, Delivery.status=="dead_letter").first()
    if not d: not_found("Dead letter")
    return serialize_delivery(requeue_dead_letter(db,d))
