import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["EVENTFLOW_API_KEY"] = "dev-secret-key"

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {
        "X-API-Key": "dev-secret-key",
    }
