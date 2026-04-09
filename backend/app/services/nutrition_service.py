from datetime import date, datetime, timedelta

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.goal import Goal
from app.models.nutrition_log import NutritionLog
from app.schemas.nutrition_schemas import (
    DaySummary,
    GoalCreate,
    GoalOut,
    NutritionLogCreate,
    NutritionLogOut,
    NutritionLogsResponse,
)

MAX_DAYS = 30


async def create_log(
    db: AsyncSession, userId: int, data: NutritionLogCreate
) -> NutritionLogOut:
    """Insert a new nutrition log entry for the given user."""
    log = NutritionLog(
        userId=userId,
        mealType=data.mealType,
        foodName=data.foodName,
        weightG=data.weightG,
        caloriesKcal=data.caloriesKcal,
        proteinG=data.proteinG,
        carbsG=data.carbsG,
        fatG=data.fatG,
        loggedAt=data.loggedAt or datetime.now(),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return NutritionLogOut.model_validate(log)


def _build_summary(
    logs: list[NutritionLog], activeGoal: Goal | None
) -> DaySummary:
    """Aggregate macros and compute deficit/surplus against active goal."""
    goalCalories = activeGoal.dailyCaloriesKcal if activeGoal else None
    totalCalories = sum(l.caloriesKcal for l in logs)
    deficitSurplus = (totalCalories - goalCalories) if goalCalories else None
    return DaySummary(
        totalCalories=totalCalories,
        totalProtein=sum(l.proteinG for l in logs),
        totalCarbs=sum(l.carbsG for l in logs),
        totalFat=sum(l.fatG for l in logs),
        goalCalories=goalCalories,
        deficitSurplus=deficitSurplus,
    )


async def get_logs(
    db: AsyncSession, userId: int, logDate: date, days: int
) -> NutritionLogsResponse:
    """Return logs in [logDate, logDate+days) with aggregated summary."""
    start = datetime(logDate.year, logDate.month, logDate.day)
    end = start + timedelta(days=days)
    result = await db.execute(
        select(NutritionLog)
        .where(
            NutritionLog.userId == userId,
            NutritionLog.loggedAt >= start,
            NutritionLog.loggedAt < end,
        )
        .order_by(NutritionLog.loggedAt)
    )
    logs = list(result.scalars().all())
    active = await _fetch_active_goal(db, userId)
    return NutritionLogsResponse(
        logs=[NutritionLogOut.model_validate(l) for l in logs],
        summary=_build_summary(logs, active),
    )


async def delete_log(db: AsyncSession, userId: int, logId: int) -> None:
    """Delete a log entry; raise 404 if missing, 403 if not the owner."""
    log = await db.get(NutritionLog, logId)
    if log is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "Log not found", "LOG_NOT_FOUND")
    if log.userId != userId:
        raise AppError(status.HTTP_403_FORBIDDEN, "Access denied", "FORBIDDEN")
    await db.delete(log)
    await db.commit()


async def create_goal(
    db: AsyncSession, userId: int, data: GoalCreate
) -> GoalOut:
    """Create a new active goal, deactivating any existing active goal."""
    existing = await db.execute(
        select(Goal).where(Goal.userId == userId, Goal.isActive.is_(True))
    )
    for g in existing.scalars().all():
        g.isActive = False
    goal = Goal(
        userId=userId,
        goalType=data.goalType,
        targetWeightKg=data.targetWeightKg,
        dailyCaloriesKcal=data.dailyCaloriesKcal,
        deadline=data.deadline,
        isActive=True,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return GoalOut.model_validate(goal)


async def _fetch_active_goal(db: AsyncSession, userId: int) -> Goal | None:
    """Return the active Goal ORM object for internal use."""
    result = await db.execute(
        select(Goal).where(Goal.userId == userId, Goal.isActive.is_(True))
    )
    return result.scalar_one_or_none()


async def get_active_goal(db: AsyncSession, userId: int) -> GoalOut | None:
    """Return the active goal schema or None."""
    goal = await _fetch_active_goal(db, userId)
    return GoalOut.model_validate(goal) if goal else None
