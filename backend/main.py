"""FastAPI application for the Mini JARVIS text assistant."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import ai_is_available, get_settings, search_key_is_configured
from backend.routes import chat, search
from backend.schemas import HealthResponse

app = FastAPI(title="AI Text Assistant — Mini JARVIS", version="1.0.0", description="A simple text AI assistant for learning and demonstration.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(chat.router)
app.include_router(search.router)


@app.get("/", tags=["status"])
async def root() -> dict[str, str]:
    return {"name": "AI Text Assistant — Mini JARVIS", "status": "online", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["status"])
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="online",
        ai_provider=settings.ai_provider.lower(),
        ai_available=ai_is_available(),
        search_available=search_key_is_configured() and settings.search_provider.lower() == "tavily",
        search_provider=settings.search_provider,
    )
