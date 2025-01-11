import pytest
from starlette.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_invalid_schema(client):
    """Test invalid schema handling"""
    response = client.get("/notes", cookies={"schema": "invalid"})
    assert response.status_code == 303  # Redirect to login


def test_missing_auth(client):
    """Test missing authentication"""
    response = client.get("/notes")
    assert response.status_code == 303  # Redirect to login


def test_invalid_audio_key(client):
    """Test invalid audio key handling"""
    response = client.get("/note_invalid")
    assert response.status_code in [404, 303]  # Not found or redirect


def test_rate_limiting(client):
    """Test rate limiting for chat"""
    # Make multiple rapid requests
    for _ in range(6):
        response = client.post(
            "/api/chat", json={"message": "test", "chat_id": "test_chat"}
        )
    assert response.status_code == 429  # Too many requests
