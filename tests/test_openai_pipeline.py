import asyncio
from types import SimpleNamespace

from backend.config import get_settings
from backend.services import ai_service


def test_ai_response_uses_configured_openai_responses_model(monkeypatch):
    calls = {}
    monkeypatch.setattr(get_settings(), "ai_provider", "openai")

    def create(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(output_text="A concise answer.")

    monkeypatch.setattr(ai_service, "_client", lambda: SimpleNamespace(responses=SimpleNamespace(create=create)))
    reply = asyncio.run(ai_service._answer_with_ai("Explain AI", "en"))
    assert reply == "A concise answer."
    assert calls["model"] == get_settings().openai_model
    assert calls["input"] == "Explain AI"
    assert calls["max_output_tokens"] == 500
