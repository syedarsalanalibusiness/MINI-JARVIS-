from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.config import get_settings
from backend import config
from backend.main import app

client = TestClient(app)


def test_health_reports_online_and_service_configuration(monkeypatch):
    monkeypatch.setattr(get_settings(), "openai_api_key", SecretStr(""))
    monkeypatch.setattr(get_settings(), "search_api_key", SecretStr(""))
    monkeypatch.setattr(get_settings(), "ai_provider", "ollama")
    monkeypatch.setattr(config, "ollama_is_available", lambda: False)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "ai_provider": "ollama",
        "ai_available": False,
        "search_available": False,
        "search_provider": "tavily",
    }
    assert "api_key" not in response.json()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_empty_chat_message_is_rejected():
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 422
