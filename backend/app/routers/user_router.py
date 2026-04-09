from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_db
from app.schemas.user_schemas import UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Return the authenticated user's profile."""
    return await user_service.get_user_profile(db, userId)


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Partially update the authenticated user's profile."""
    return await user_service.update_user_profile(db, userId, data)
