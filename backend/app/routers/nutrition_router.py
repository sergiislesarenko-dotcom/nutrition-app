from datetime import date as date_type

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_db
from app.schemas.nutrition_schemas import (
    GoalCreate,
    GoalOut,
    NutritionLogCreate,
    NutritionLogOut,
    NutritionLogsResponse,
)
from app.services import nutrition_service

router = APIRouter(tags=["nutrition"])


@router.post("/nutrition/logs", response_model=NutritionLogOut, status_code=status.HTTP_201_CREATED)
async def create_log(
    data: NutritionLogCreate,
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NutritionLogOut:
    """Log a new meal entry."""
    return await nutrition_service.create_log(db, userId, data)


@router.get("/nutrition/logs", response_model=NutritionLogsResponse)
async def get_logs(
    log_date: date_type = Query(default_factory=date_type.today, alias="date"),
    days: int = Query(default=1, ge=1, le=30),
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NutritionLogsResponse:
    """Return logs and daily summary for the given date range."""
    return await nutrition_service.get_logs(db, userId, log_date, days)


@router.delete("/nutrition/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    log_id: int,
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Delete a nutrition log entry."""
    await nutrition_service.delete_log(db, userId, log_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
async def create_goal(
    data: GoalCreate,
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    """Create a new goal, deactivating the previous one."""
    return await nutrition_service.create_goal(db, userId, data)


@router.get("/goals/active", response_model=GoalOut | None)
async def get_active_goal(
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> GoalOut | None:
    """Return the current active goal, or null if none exists."""
    return await nutrition_service.get_active_goal(db, userId)
