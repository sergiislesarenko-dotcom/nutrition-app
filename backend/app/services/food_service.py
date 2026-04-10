import json

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.food import Food
from app.schemas.food_schemas import FoodCompleteRequest, FoodMacrosOut, FoodOut, FoodSearchResponse
from app.services.ai_service import AI_MODEL, _make_client

FOOD_LOOKUP_MAX_TOKENS = 100


async def search_foods(
    db: AsyncSession, query: str, limit: int = 10
) -> FoodSearchResponse:
    """Return up to `limit` foods whose name contains `query`."""
    result = await db.execute(
        select(Food)
        .where(Food.name.like(f"%{query.strip().lower()}%"))
        .limit(limit)
    )
    foods = result.scalars().all()
    return FoodSearchResponse(results=[FoodOut.model_validate(f) for f in foods])


async def get_food_macros(
    db: AsyncSession, foodName: str, weightG: float
) -> FoodMacrosOut:
    """Find or AI-create a food record, then calculate macros for weightG."""
    normalizedName = foodName.strip().lower()
    food = await _find_food(db, normalizedName)
    if food is None:
        macros = await _fetch_from_ai(foodName)
        food = await _save_food(db, normalizedName, macros)
    return _calculate_macros(food, weightG)


async def _find_food(db: AsyncSession, normalizedName: str) -> Food | None:
    """Exact case-insensitive lookup by normalized name."""
    result = await db.execute(select(Food).where(Food.name == normalizedName))
    return result.scalar_one_or_none()


async def _fetch_from_ai(foodName: str) -> dict:
    """Call Claude to get per-100g macros; return validated dict."""
    client = _make_client()
    response = await client.messages.create(
        model=AI_MODEL,
        max_tokens=FOOD_LOOKUP_MAX_TOKENS,
        messages=[{"role": "user", "content": _build_food_prompt(foodName)}],
    )
    raw = response.content[0].text.strip()
    return _parse_and_validate_macros(raw, foodName)


def _build_food_prompt(foodName: str) -> str:
    """Return a focused prompt for Claude to produce structured nutrition data."""
    return (
        "Return ONLY valid JSON, no explanation, no markdown, no extra text.\n"
        'Format: {"calories_per_100g": N, "protein_per_100g": N, '
        '"carbs_per_100g": N, "fat_per_100g": N}\n'
        f"Food: {foodName}\n"
        "Provide typical average nutritional values per 100g. "
        "All values must be non-negative numbers."
    )


def _parse_and_validate_macros(raw: str, foodName: str) -> dict:
    """Parse AI JSON response and validate all required macro fields."""
    required = {"calories_per_100g", "protein_per_100g", "carbs_per_100g", "fat_per_100g"}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise AppError(502, f"AI returned unparseable data for '{foodName}'", "AI_PARSE_ERROR")
    if not required.issubset(data.keys()):
        raise AppError(502, f"AI returned incomplete data for '{foodName}'", "AI_INVALID_RESPONSE")
    if any(not isinstance(data[k], (int, float)) or data[k] < 0 for k in required):
        raise AppError(502, f"AI returned invalid values for '{foodName}'", "AI_INVALID_RESPONSE")
    return {k: float(data[k]) for k in required}


async def _save_food(db: AsyncSession, name: str, macros: dict) -> Food:
    """Persist a new Food row; handle race condition via IntegrityError."""
    food = Food(
        name=name,
        caloriesPer100g=macros["calories_per_100g"],
        proteinPer100g=macros["protein_per_100g"],
        carbsPer100g=macros["carbs_per_100g"],
        fatPer100g=macros["fat_per_100g"],
    )
    try:
        db.add(food)
        await db.commit()
        await db.refresh(food)
        return food
    except IntegrityError:
        await db.rollback()
        existing = await _find_food(db, name)
        if existing is None:
            raise AppError(500, "Failed to save food record", "DB_ERROR")
        return existing


async def complete_food_macros(
    db: AsyncSession, name: str, weightG: float, known: dict
) -> FoodMacrosOut:
    """Complete partial macros via AI or formula, upsert to DB, return scaled values."""
    normalizedName = name.strip().lower()
    ALL_BJU = {"protein_per_100g", "carbs_per_100g", "fat_per_100g"}
    missingBju = ALL_BJU - set(known.keys())
    if missingBju:
        aiFields = await _fetch_partial_from_ai(name, known, missingBju)
        completeBju = {**aiFields, **{k: known[k] for k in known if k in ALL_BJU}}
    else:
        completeBju = {k: known[k] for k in ALL_BJU}
    fullMacros = {
        **completeBju,
        "calories_per_100g": _calc_calories(
            completeBju["protein_per_100g"],
            completeBju["carbs_per_100g"],
            completeBju["fat_per_100g"],
        ),
    }
    food = await _upsert_food(db, normalizedName, fullMacros)
    return _calculate_macros(food, weightG)


async def _fetch_partial_from_ai(foodName: str, known: dict, missing: set) -> dict:
    """Call Claude to return only the missing macro fields given known context."""
    client = _make_client()
    prompt = _build_completion_prompt(foodName, known, missing)
    response = await client.messages.create(
        model=AI_MODEL,
        max_tokens=FOOD_LOOKUP_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    return _parse_partial_macros(raw, foodName, missing)


def _build_completion_prompt(foodName: str, known: dict, missing: set) -> str:
    """Build prompt asking Claude to fill only the missing per-100g macro fields."""
    knownLines = ", ".join(
        f"{k.replace('_per_100g', '')}={v}g" for k, v in known.items()
    )
    missingJson = "{" + ", ".join(f'"{k}": N' for k in sorted(missing)) + "}"
    return (
        f"Food: {foodName}\n"
        f"Known values per 100g: {knownLines}\n"
        "Provide ONLY the missing values in JSON format.\n"
        f"Return ONLY valid JSON: {missingJson}\n"
        "All values must be non-negative numbers."
    )


def _parse_partial_macros(raw: str, foodName: str, required: set) -> dict:
    """Parse AI JSON for partial fields; validate presence and non-negative values."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise AppError(502, f"AI returned unparseable data for '{foodName}'", "AI_PARSE_ERROR")
    if not required.issubset(data.keys()):
        raise AppError(502, f"AI returned incomplete data for '{foodName}'", "AI_INVALID_RESPONSE")
    if any(not isinstance(data[k], (int, float)) or data[k] < 0 for k in required):
        raise AppError(502, f"AI returned invalid values for '{foodName}'", "AI_INVALID_RESPONSE")
    return {k: float(data[k]) for k in required}


def _calc_calories(protein: float, carbs: float, fat: float) -> float:
    """Atwater formula: protein/carbs = 4 kcal/g, fat = 9 kcal/g."""
    return round(protein * 4 + carbs * 4 + fat * 9, 1)


async def _upsert_food(db: AsyncSession, name: str, macros: dict) -> Food:
    """Insert or update a Food row by name; always reflects the latest provided values."""
    food = await _find_food(db, name)
    if food is not None:
        food.caloriesPer100g = macros["calories_per_100g"]
        food.proteinPer100g = macros["protein_per_100g"]
        food.carbsPer100g = macros["carbs_per_100g"]
        food.fatPer100g = macros["fat_per_100g"]
        await db.commit()
        await db.refresh(food)
        return food
    return await _save_food(db, name, macros)


def _calculate_macros(food: Food, weightG: float) -> FoodMacrosOut:
    """Scale per-100g values to the requested weight; recalculate calories if stored as 0."""
    factor = weightG / 100.0
    caloriesPer100g = food.caloriesPer100g
    if caloriesPer100g == 0 and (food.proteinPer100g > 0 or food.carbsPer100g > 0 or food.fatPer100g > 0):
        caloriesPer100g = _calc_calories(food.proteinPer100g, food.carbsPer100g, food.fatPer100g)
    return FoodMacrosOut(
        food=FoodOut.model_validate(food),
        weightG=weightG,
        caloriesKcal=round(caloriesPer100g * factor, 1),
        proteinG=round(food.proteinPer100g * factor, 1),
        carbsG=round(food.carbsPer100g * factor, 1),
        fatG=round(food.fatPer100g * factor, 1),
    )
