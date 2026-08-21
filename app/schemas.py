from typing import Any
from pydantic import BaseModel, Field, HttpUrl

class EventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=128)
    source: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]

class SubscriptionCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=128)
    target_url: HttpUrl

class SubscriptionUpdate(BaseModel):
    active: bool
