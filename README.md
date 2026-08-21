# EventFlow API Platform

Production style event ingestion and webhook delivery service with idempotency, replay, retries, dead letter recovery, subscriptions, persistence, and operational endpoints.

![CI](https://img.shields.io/badge/tests-11%20passing-success)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API contract.

## Deployment

The repository includes Docker and Render configuration. The service exposes `/health` for platform health checks.

## Detailed notes

# EventFlow API Platform

Production style event ingestion and webhook delivery service with idempotency, replay, retries, dead letter recovery, subscriptions, persistence, and operational endpoints.

![CI](https://img.shields.io/badge/tests-11%20passing-success)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API contract.

## Deployment

The repository includes Docker and Render configuration. The service exposes `/health` for platform health checks.

## Detailed notes

# EventFlow API Platform

A production style event ingestion and delivery service built with FastAPI.

## What it demonstrates

1. Typed REST API design
2. Idempotent event ingestion
3. PostgreSQL ready persistence through SQLAlchemy
4. Background event processing
5. Webhook subscriptions
6. Retry tracking and delivery state
7. Dead letter handling
8. API key authentication
9. Structured health and metrics endpoints
10. Pagination and filtering
11. Docker support
12. Automated tests

## Architecture

```text
Producer
    |
    v
FastAPI
    |
    v
Authentication
    |
    v
Idempotency Check
    |
    v
Event Store
    |
    v
Background Processor
    |
    v
Subscription Matching
    |
    v
Webhook Delivery
    |
    +---- success ----> Delivered
    |
    +---- failure ----> Retry ----> Dead Letter
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Start the API

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Run tests

```bash
pytest -q
```

## Authentication

Use the default development key:

```text
dev-secret-key
```

Pass it in:

```text
X-API-Key
```

## Example event

```json
{
  "event_type": "customer.created",
  "source": "crm",
  "payload": {
    "customer_id": "cus_123",
    "plan": "premium"
  }
}
```

## Idempotency

Pass an idempotency key using:

```text
Idempotency-Key
```

Sending the same event twice with the same key returns the original event instead of inserting a duplicate.

## Recruiter summary

Built a production style event processing API with typed contracts, idempotent ingestion, persistent event storage, webhook subscriptions, retry tracking, dead letter handling, API authentication, observability endpoints, and automated integration tests.
