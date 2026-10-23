"""Application settings loaded from environment variables or .env."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    ai_provider: str = "murakumo"
    murakumo_base_url: str = "https://api.murakumo.cloud/v1"
    murakumo_model: str = "mishima"
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-5.6-luna"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma3:1b"
    search_api_key: SecretStr = SecretStr("")
    backend_api_token: SecretStr = SecretStr("")
    search_provider: str = "tavily"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def openai_key_is_configured() -> bool:
    """Report key presence without returning or logging the secret itself."""
    return bool(get_settings().openai_api_key.get_secret_value().strip())


def get_openai_api_key() -> str:
    """Return the key for server-side SDK initialization only."""
    return get_settings().openai_api_key.get_secret_value().strip()


def search_key_is_configured() -> bool:
    return bool(get_settings().search_api_key.get_secret_value().strip())


def get_search_api_key() -> str:
    """Return the key for server-side requests only."""
    return get_settings().search_api_key.get_secret_value().strip()


def ollama_is_available() -> bool:
    """Check that the local Ollama service and configured model are ready."""
    import httpx

    settings = get_settings()
    try:
        response = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=1.5)
        response.raise_for_status()
        installed = {item.get("name", "") for item in response.json().get("models", [])}
        return settings.ollama_model in installed
    except (httpx.HTTPError, ValueError, TypeError):
        return False


def murakumo_is_available() -> bool:
    """Check the keyless hosted chat model catalog without sending user content."""
    import httpx

    settings = get_settings()
    try:
        response = httpx.get(f"{settings.murakumo_base_url.rstrip('/')}/models", timeout=4.0, trust_env=False)
        response.raise_for_status()
        models = response.json().get("data", [])
        return any(
            item.get("id") == settings.murakumo_model and item.get("is_ready") is True
            for item in models
        )
    except (httpx.HTTPError, ValueError, TypeError):
        return False


def ai_is_available() -> bool:
    settings = get_settings()
    provider = settings.ai_provider.lower()
    if provider == "ollama":
        return ollama_is_available()
    if provider == "murakumo":
        return murakumo_is_available()
    if provider == "openai":
        return openai_key_is_configured()
    return False
