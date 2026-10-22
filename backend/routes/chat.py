"""Text chat endpoint."""

from fastapi import APIRouter, Depends, HTTPException

from backend.schemas import ChatRequest, ChatResponse
from backend.services.ai_service import AIServiceError, answer_message
from backend.security import require_backend_token

router = APIRouter(dependencies=[Depends(require_backend_token)])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Please enter a message first.")
    try:
        reply, language, intent = await answer_message(request.message.strip())
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ChatResponse(reply=reply, language=language, intent=intent)
