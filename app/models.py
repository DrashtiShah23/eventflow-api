from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    source: Mapped[str] = mapped_column(String(128), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    target_url: Mapped[str] = mapped_column(String(512))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    subscription_id: Mapped[str] = mapped_column(String(64), index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
