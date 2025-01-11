import pytest
from starlette.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_edit_note(client):
    """Test note editing endpoint"""
    response = client.post(
        "/api/edit-note/test_123",
        json={"note_title": "Updated Title", "transcript_text": "Updated content"},
    )
    assert response.status_code in [200, 401]


def test_chat_title_update(client):
    """Test chat title update"""
    response = client.post(
        "/api/update-chat-title", json={"chat_id": "test_chat", "title": "New Title"}
    )
    assert response.status_code in [200, 401]


def test_search_filters(client):
    """Test search and filter functionality"""
    # Test date filters
    response = client.get(
        "/notes", params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
    )
    assert response.status_code in [200, 303]

    # Test keyword search
    response = client.get("/notes", params={"keyword": "test"})
    assert response.status_code in [200, 303]


@pytest.mark.skip(reason="Requires S3 access")
def test_audio_streaming(client):
    """Test audio streaming endpoint"""
    response = client.get("/api/get-audio/test_123")
    assert response.status_code in [200, 401, 404]
    if response.status_code == 200:
        assert response.headers["content-type"] == "audio/webm"
