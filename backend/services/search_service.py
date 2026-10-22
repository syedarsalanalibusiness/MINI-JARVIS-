"""Tavily web-search adapter, kept separate from assistant reasoning."""

import httpx

from backend.config import get_search_api_key, get_settings

TAVILY_URL = "https://api.tavily.com/search"


class SearchUnavailableError(RuntimeError):
    """Raised when search has no configured provider credentials."""


async def search_web(query: str) -> list[dict[str, str]]:
    settings = get_settings()
    api_key = get_search_api_key()
    if settings.search_provider.lower() != "tavily" or not api_key:
        raise SearchUnavailableError("Web search is not configured. Add a Tavily API key as SEARCH_API_KEY in .env.")
    payload = {"api_key": api_key, "query": query, "max_results": 5, "search_depth": "basic"}
    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.post(TAVILY_URL, json=payload)
        response.raise_for_status()
        data = response.json()
    return [
        {"title": str(item.get("title", ""))[:300], "url": str(item.get("url", ""))[:1000], "content": str(item.get("content", ""))[:2000]}
        for item in data.get("results", [])[:5]
    ]
