from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Schema for AI chat request."""

    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    """Schema for non-streaming AI chat response."""

    answer: str
    recommendationId: int = Field(serialization_alias="recommendation_id")


class RecommendationOut(BaseModel):
    """Schema for a stored recommendation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    createdAt: datetime = Field(serialization_alias="created_at")


class RecommendationsListResponse(BaseModel):
    """Schema for paginated recommendations list."""

    items: list[RecommendationOut]
    total: int
