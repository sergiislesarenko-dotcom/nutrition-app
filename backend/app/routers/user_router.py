from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_db
from app.schemas.nutrition_schemas import RestrictionCreate, RestrictionOut
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


@router.post("/me/restrictions", response_model=RestrictionOut, status_code=status.HTTP_201_CREATED)
async def add_restriction(
    data: RestrictionCreate,
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> RestrictionOut:
    """Add a dietary, medical, or allergy restriction."""
    return await user_service.add_restriction(db, userId, data)


@router.get("/me/restrictions", response_model=list[RestrictionOut])
async def get_restrictions(
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[RestrictionOut]:
    """Return all restrictions for the authenticated user."""
    return await user_service.get_restrictions(db, userId)


@router.delete("/me/restrictions/{restriction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restriction(
    restriction_id: int,
    userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Delete a restriction by ID."""
    await user_service.delete_restriction(db, userId, restriction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
