from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_db
from app.schemas.ai_schemas import ChatRequest, ChatResponse, RecommendationsListResponse
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Send a message to the AI assistant (non-streaming)."""
    return await ai_service.chat(db, userId, data.message)


@router.post("/chat/stream")
async def chat_stream(
    data: ChatRequest,
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream an AI response as Server-Sent Events."""
    return StreamingResponse(
        ai_service.chat_stream(db, userId, data.message),
        media_type="text/event-stream",
    )


@router.get("/recommendations", response_model=RecommendationsListResponse)
async def get_recommendations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> RecommendationsListResponse:
    """Return paginated AI recommendation history."""
    return await ai_service.get_recommendations(db, userId, limit, offset)
