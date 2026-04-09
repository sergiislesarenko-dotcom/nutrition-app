from datetime import date
from typing import AsyncGenerator

from anthropic import AsyncAnthropic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.goal import Goal
from app.models.recommendation import Recommendation
from app.models.restriction import Restriction
from app.models.user import User
from app.schemas.ai_schemas import ChatResponse, RecommendationOut, RecommendationsListResponse
from app.services.nutrition_service import get_logs
from app.services.prompt_builder import build_system_prompt
from app.services.user_service import calculate_bmi, calculate_tdee

AI_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024


def _make_client() -> AsyncAnthropic:
    """Instantiate the Anthropic async client."""
    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


async def _gather_context(db: AsyncSession, userId: int) -> tuple:
    """Fetch user profile, active goal, restrictions, and today's logs."""
    user = await db.get(User, userId)
    goal_result = await db.execute(
        select(Goal).where(Goal.userId == userId, Goal.isActive.is_(True))
    )
    goal = goal_result.scalar_one_or_none()
    restr_result = await db.execute(
        select(Restriction).where(Restriction.userId == userId)
    )
    restrictions = list(restr_result.scalars().all())
    logs_resp = await get_logs(db, userId, date.today(), 1)
    bmi = calculate_bmi(user.weightKg, user.heightCm)
    tdee = calculate_tdee(user.weightKg, user.heightCm, user.age, user.gender, user.activityLevel)
    return user, goal, restrictions, logs_resp.logs, bmi, tdee


async def _save_recommendation(
    db: AsyncSession, userId: int, question: str, answer: str
) -> Recommendation:
    """Persist a Q&A pair to the recommendations table."""
    rec = Recommendation(userId=userId, question=question, answer=answer)
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


async def chat(db: AsyncSession, userId: int, message: str) -> ChatResponse:
    """Send a non-streaming message to Claude and store the response."""
    user, goal, restrictions, logs, bmi, tdee = await _gather_context(db, userId)
    system = build_system_prompt(user, goal, restrictions, logs, bmi, tdee)
    client = _make_client()
    response = await client.messages.create(
        model=AI_MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": message}],
    )
    answer = response.content[0].text
    rec = await _save_recommendation(db, userId, message, answer)
    return ChatResponse(answer=answer, recommendationId=rec.id)


async def chat_stream(
    db: AsyncSession, userId: int, message: str
) -> AsyncGenerator[str, None]:
    """Yield SSE chunks from Claude; persist the full answer after streaming."""
    user, goal, restrictions, logs, bmi, tdee = await _gather_context(db, userId)
    system = build_system_prompt(user, goal, restrictions, logs, bmi, tdee)
    client = _make_client()
    full_answer: list[str] = []
    async with client.messages.stream(
        model=AI_MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": message}],
    ) as stream:
        async for text in stream.text_stream:
            full_answer.append(text)
            yield f"data: {text}\n\n"
    await _save_recommendation(db, userId, message, "".join(full_answer))
    yield "data: [DONE]\n\n"


async def get_recommendations(
    db: AsyncSession, userId: int, limit: int, offset: int
) -> RecommendationsListResponse:
    """Return paginated recommendation history for the user."""
    total_result = await db.execute(
        select(func.count()).where(Recommendation.userId == userId)
    )
    total = total_result.scalar_one()
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.userId == userId)
        .order_by(Recommendation.createdAt.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [RecommendationOut.model_validate(r) for r in result.scalars().all()]
    return RecommendationsListResponse(items=items, total=total)
