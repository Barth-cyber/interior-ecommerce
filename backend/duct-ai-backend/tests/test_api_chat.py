import json

from app import app


def test_api_chat_basic():
    client = app.test_client()
    payload = {
        "messages": [{"role": "user", "content": "Hello, can you help me?"}],
        "session_id": "test-session"
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert "reply" in data
    assert "actions" in data
    assert "provider" in data
    assert data["reply"] is None or isinstance(data["reply"], str)


def test_config_endpoint():
    client = app.test_client()
    resp = client.get("/config")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert "allowed_origins" in data or "analytics" in data
