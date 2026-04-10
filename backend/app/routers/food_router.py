from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_db
from app.schemas.food_schemas import FoodCompleteRequest, FoodMacrosOut, FoodSearchResponse
from app.services import food_service

router = APIRouter(tags=["foods"])


@router.get("/foods/search", response_model=FoodSearchResponse)
async def search_foods(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=10, ge=1, le=25),
    db: AsyncSession = Depends(get_db),
) -> FoodSearchResponse:
    """Search food names for autocomplete. No auth required (global data)."""
    return await food_service.search_foods(db, q, limit)


@router.get("/foods/macros", response_model=FoodMacrosOut)
async def get_food_macros(
    name: str = Query(min_length=1, max_length=255),
    weight: float = Query(gt=0),
    # Auth enforced to prevent AI abuse; userId not used (food data is global)
    _userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> FoodMacrosOut:
    """Return calculated macros for a food at the given weight.
    Triggers a one-time AI lookup if the food is not yet in the database.
    Subsequent calls return cached DB values without calling AI.
    """
    return await food_service.get_food_macros(db, name, weight)


@router.post("/foods/complete", response_model=FoodMacrosOut)
async def complete_food_macros(
    body: FoodCompleteRequest,
    _userId: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> FoodMacrosOut:
    """Complete partial macro data using AI or Atwater formula; upsert food and return macros."""
    known = {k: v for k, v in body.known.model_dump().items() if v is not None}
    return await food_service.complete_food_macros(db, body.name, body.weight_g, known)
