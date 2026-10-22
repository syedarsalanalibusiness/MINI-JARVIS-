from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.config import get_settings
from backend.main import app
from backend.services import ai_service, command_service

client = TestClient(app)


def test_local_date_command_needs_no_api_key():
    response = client.post("/chat", json={"message": "What is today's date?"})
    assert response.status_code == 200
    assert response.json()["intent"] == "date"
    assert "date" in response.json()["reply"].lower()


def test_deployment_token_protects_chat_but_not_health(monkeypatch):
    from pydantic import SecretStr

    settings = get_settings()
    monkeypatch.setattr(settings, "backend_api_token", SecretStr("test-deployment-token"))
    assert client.get("/health").status_code == 200
    assert client.post("/chat", json={"message": "Hello JARVIS"}).status_code == 401
    response = client.post(
        "/chat",
        json={"message": "Hello JARVIS"},
        headers={"Authorization": "Bearer test-deployment-token"},
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "greeting"


def test_calculator_command():
    reply, intent = command_service.handle_local_command("Calculate 125 divided by 5.", "en")
    assert (reply, intent) == ("The answer is 25.", "calculator")


def test_command_detection_and_search_query():
    assert command_service.handle_local_command("Hello JARVIS", "en")[1] == "greeting"
    assert command_service.is_search_request("Search the web for Python latest news")
    assert command_service.extract_search_query("Search the web for Python latest news") == "Python"


def test_ai_unconfigured_returns_friendly_error(monkeypatch):
    monkeypatch.setattr(get_settings(), "openai_api_key", SecretStr(""))
    monkeypatch.setattr(get_settings(), "ai_provider", "openai")
    response = client.post("/chat", json={"message": "Explain machine learning."})
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_ai_sdk_errors_become_friendly_errors(monkeypatch):
    from openai import APIConnectionError

    def broken_client():
        raise APIConnectionError(request=None)

    monkeypatch.setattr(ai_service, "_client", broken_client)
    monkeypatch.setattr(get_settings(), "ai_provider", "openai")
    try:
        import asyncio

        asyncio.run(ai_service._answer_with_ai("hello", "en"))
    except ai_service.AIServiceError as exc:
        assert "internet connection" in str(exc)
    else:
        raise AssertionError("Expected AI connection failure to be translated")


def test_local_ollama_chat_uses_configured_model(monkeypatch):
    import asyncio
    import httpx

    monkeypatch.setattr(get_settings(), "ai_provider", "ollama")
    monkeypatch.setattr(get_settings(), "ollama_model", "gemma3:1b")
    monkeypatch.setattr(ai_service, "ollama_is_available", lambda: True)
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: httpx.Response(200, request=httpx.Request("POST", args[0]), json={"message": {"content": "A friendly local answer."}}))
    reply = asyncio.run(ai_service._answer_with_ai("Hello", "en"))
    assert reply == "A friendly local answer."


def test_murakumo_chat_uses_configured_public_model(monkeypatch):
    import asyncio
    import httpx

    settings = get_settings()
    monkeypatch.setattr(settings, "ai_provider", "murakumo")
    monkeypatch.setattr(settings, "murakumo_model", "mishima")
    monkeypatch.setattr(ai_service, "murakumo_is_available", lambda: True)
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(
            200,
            request=httpx.Request("POST", args[0]),
            json={"choices": [{"message": {"content": "A hosted answer."}}]},
        ),
    )
    reply = asyncio.run(ai_service._answer_with_ai("Explain AI", "en"))
    assert reply == "A hosted answer."


def test_url_extraction_and_private_link_block():
    import pytest

    from backend.services.webpage_service import PageFetchError, _validate_public_url, find_url

    assert find_url("Please review https://example.com/sale?id=2.") == "https://example.com/sale?id=2"
    with pytest.raises(PageFetchError, match="public websites"):
        _validate_public_url("http://127.0.0.1/private")
