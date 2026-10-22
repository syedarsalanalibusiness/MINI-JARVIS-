from pydantic import SecretStr

from backend.config import ENV_FILE, PROJECT_ROOT, get_settings, openai_key_is_configured


def test_env_file_is_resolved_from_project_root_outside_current_directory(monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT.parent)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("BACKEND_API_TOKEN", raising=False)
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert ENV_FILE == PROJECT_ROOT / ".env"
        assert ENV_FILE.is_absolute()
        assert settings.openai_model.strip()
        assert openai_key_is_configured() == bool(settings.openai_api_key.get_secret_value().strip())
    finally:
        get_settings.cache_clear()


def test_openai_client_is_initialized_when_key_is_configured(monkeypatch):
    from backend.services import ai_service

    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    get_settings.cache_clear()
    try:
        assert openai_key_is_configured()
        assert "test-only-not-a-real-key" not in repr(get_settings())
        client = ai_service._client()
        assert hasattr(client.responses, "create")
    finally:
        get_settings.cache_clear()


def test_env_example_does_not_contain_a_key():
    example = PROJECT_ROOT / ".env.example"
    values = {}
    for line in example.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            values[name.strip()] = value.strip()
    assert values["OPENAI_API_KEY"] == ""
    assert values["OPENAI_MODEL"] == "gpt-5.6-luna"
    assert values["BACKEND_API_TOKEN"] == ""
