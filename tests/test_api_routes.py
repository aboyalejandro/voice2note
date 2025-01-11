import pytest
from starlette.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_login_endpoint(client):
    """Test login endpoint"""
    response = client.post(
        "/api/login", data={"username": "test_user", "password": "test_pass"}
    )
    assert response.status_code in [200, 303]  # Success or redirect


def test_save_audio_endpoint(client):
    """Test audio upload endpoint"""
    # Mock audio file
    files = {"audio_file": ("test.webm", b"test audio content", "audio/webm")}
    data = {"audio_type": "recorded"}

    response = client.post("/api/save-audio", files=files, data=data)
    assert response.status_code in [200, 401]  # Success or unauthorized


def test_invalid_endpoints(client):
    """Test invalid endpoint handling"""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404
