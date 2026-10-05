"""
Pytest configuration for AgroVision AI Backend.
Sets up the test client so all tests use in-memory dev fallback
without needing a live Supabase connection.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="session")
def client():
    """Session-scoped FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Register a test user and return Bearer auth headers."""
    reg = client.post("/api/auth/register", json={
        "full_name": "Test Farmer",
        "email": "testfarmer@pytest.com",
        "password": "TestPass123!"
    })
    token = reg.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    """Login as the built-in dev admin and return Bearer auth headers."""
    login = client.post("/api/auth/login", json={
        "email": "admin@agrovision.ai",
        "password": "adminSecretPassword!"
    })
    token = login.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}
