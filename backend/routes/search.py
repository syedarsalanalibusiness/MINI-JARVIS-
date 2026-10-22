"""Explicit web search endpoint."""

from fastapi import APIRouter, Depends

from backend.config import get_settings
from backend.schemas import SearchRequest, SearchResponse
from backend.services.search_service import SearchUnavailableError, search_web
from backend.security import require_backend_token

router = APIRouter(dependencies=[Depends(require_backend_token)])


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    if not request.query.strip():
        return SearchResponse(results=[], available=False, message="Enter a search query.")
    if not get_settings().search_api_key:
        return SearchResponse(results=[], available=False, message="Web search is unavailable until SEARCH_API_KEY is configured in .env.")
    try:
        results = await search_web(request.query.strip())
    except SearchUnavailableError as exc:
        return SearchResponse(results=[], available=False, message=str(exc))
    except Exception:
        return SearchResponse(results=[], available=False, message="Web search failed. Check your connection and Tavily API key, then try again.")
    return SearchResponse(results=results, available=True, message="Search complete.")
