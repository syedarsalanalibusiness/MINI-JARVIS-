"""Validated API request and response models."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    language: str
    intent: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class SearchResponse(BaseModel):
    results: list[dict[str, str]]
    available: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    ai_provider: str
    ai_available: bool
    search_available: bool
    search_provider: str
