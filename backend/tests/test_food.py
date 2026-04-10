from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import Food
from app.core.exceptions import AppError
from app.services.food_service import _upsert_food

pytestmark = pytest.mark.asyncio(loop_scope="session")

BASE = "/api/v1"

# ---------------------------------------------------------------------------
# Shared AI response data
# ---------------------------------------------------------------------------

FULL_AI_MACROS = {
    "calories_per_100g": 165.0,
    "protein_per_100g": 31.0,
    "carbs_per_100g": 0.0,
    "fat_per_100g": 3.6,
}

# AI returns only the two missing fields (protein + carbs) when fat is known
PARTIAL_AI_MACROS = {
    "protein_per_100g": 18.0,
    "carbs_per_100g": 3.0,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_full_ai(mocker) -> AsyncMock:
    """Patch _fetch_from_ai (GET /foods/macros path)."""
    return mocker.patch(
        "app.services.food_service._fetch_from_ai",
        new_callable=AsyncMock,
        return_value=FULL_AI_MACROS,
    )


def _mock_partial_ai(mocker, response: dict | None = None) -> AsyncMock:
    """Patch _fetch_partial_from_ai (POST /foods/complete path)."""
    return mocker.patch(
        "app.services.food_service._fetch_partial_from_ai",
        new_callable=AsyncMock,
        return_value=response or PARTIAL_AI_MACROS,
    )


async def _seed_food(
    db: AsyncSession,
    name: str = "chicken breast",
    calories: float = 165.0,
    protein: float = 31.0,
    carbs: float = 0.0,
    fat: float = 3.6,
) -> Food:
    """Insert a Food row directly; used to bypass AI in DB-hit tests."""
    food = Food(
        name=name,
        caloriesPer100g=calories,
        proteinPer100g=protein,
        carbsPer100g=carbs,
        fatPer100g=fat,
    )
    db.add(food)
    await db.commit()
    await db.refresh(food)
    return food


# ---------------------------------------------------------------------------
# GET /foods/search
# ---------------------------------------------------------------------------


class TestFoodSearch:
    """GET /foods/search — public endpoint, searches by name substring."""

    async def test_empty_db_returns_empty_list(self, client: AsyncClient):
        """Empty DB → empty results array."""
        r = await client.get(f"{BASE}/foods/search", params={"q": "chicken"})
        assert r.status_code == 200
        assert r.json()["results"] == []

    async def test_finds_matching_food(self, client: AsyncClient, db_session: AsyncSession):
        """Partial match returns the food record."""
        await _seed_food(db_session, name="chicken breast")
        r = await client.get(f"{BASE}/foods/search", params={"q": "chick"})
        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) == 1
        assert results[0]["name"] == "chicken breast"

    async def test_search_is_case_insensitive(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Upper-case query still finds a lower-case DB record."""
        await _seed_food(db_session, name="cottage cheese")
        r = await client.get(f"{BASE}/foods/search", params={"q": "Cottage"})
        assert r.status_code == 200
        assert len(r.json()["results"]) == 1

    async def test_no_match_returns_empty(self, client: AsyncClient, db_session: AsyncSession):
        """Query with no match returns empty results."""
        await _seed_food(db_session, name="apple")
        r = await client.get(f"{BASE}/foods/search", params={"q": "xyz999"})
        assert r.status_code == 200
        assert r.json()["results"] == []

    async def test_limit_param_respected(self, client: AsyncClient, db_session: AsyncSession):
        """limit param caps the result count."""
        for i in range(5):
            await _seed_food(db_session, name=f"food item {i}")
        r = await client.get(f"{BASE}/foods/search", params={"q": "food", "limit": 3})
        assert r.status_code == 200
        assert len(r.json()["results"]) <= 3

    async def test_no_auth_required(self, client: AsyncClient):
        """No Authorization header → 200 (public endpoint)."""
        r = await client.get(f"{BASE}/foods/search", params={"q": "any"})
        assert r.status_code == 200

    async def test_food_record_fields_present(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Response includes all expected per-100g fields."""
        await _seed_food(db_session, name="rice")
        r = await client.get(f"{BASE}/foods/search", params={"q": "rice"})
        food = r.json()["results"][0]
        for field in ("id", "name", "calories_per_100g", "protein_per_100g", "carbs_per_100g", "fat_per_100g"):
            assert field in food


# ---------------------------------------------------------------------------
# GET /foods/macros
# ---------------------------------------------------------------------------


class TestFoodMacros:
    """GET /foods/macros — triggers AI on first call, uses DB cache after."""

    async def test_ai_called_for_unknown_food(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """First request for unknown food triggers AI and returns macros."""
        mock = _mock_full_ai(mocker)
        r = await client.get(
            f"{BASE}/foods/macros",
            params={"name": "chicken breast", "weight": 200},
            headers=auth_headers,
        )
        assert r.status_code == 200
        mock.assert_called_once()
        body = r.json()
        assert body["calories_kcal"] > 0
        assert body["protein_g"] > 0
        assert body["weight_g"] == 200.0

    async def test_ai_not_called_for_cached_food(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mocker
    ):
        """Second request for same food does not call AI (served from DB)."""
        await _seed_food(db_session, name="chicken breast")
        mock = _mock_full_ai(mocker)
        r = await client.get(
            f"{BASE}/foods/macros",
            params={"name": "chicken breast", "weight": 150},
            headers=auth_headers,
        )
        assert r.status_code == 200
        mock.assert_not_called()

    async def test_macros_scaled_by_weight(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mocker
    ):
        """Returned macros are correctly scaled to the requested weight."""
        mocker.patch(
            "app.services.food_service._fetch_from_ai",
            new_callable=AsyncMock,
            return_value={
                "calories_per_100g": 100.0,
                "protein_per_100g": 10.0,
                "carbs_per_100g": 5.0,
                "fat_per_100g": 4.0,
            },
        )
        r = await client.get(
            f"{BASE}/foods/macros",
            params={"name": "test food", "weight": 200},
            headers=auth_headers,
        )
        body = r.json()
        assert body["calories_kcal"] == pytest.approx(200.0, abs=0.1)
        assert body["protein_g"] == pytest.approx(20.0, abs=0.1)
        assert body["carbs_g"] == pytest.approx(10.0, abs=0.1)
        assert body["fat_g"] == pytest.approx(8.0, abs=0.1)

    async def test_calories_zero_in_db_uses_formula_fallback(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mocker
    ):
        """Food with calories=0 in DB gets calories recalculated by Atwater formula."""
        # Seed food with protein=10, carbs=5, fat=4 per 100g but calories=0 (bad data)
        await _seed_food(db_session, name="stale food", calories=0.0, protein=10.0, carbs=5.0, fat=4.0)
        mocker.patch(
            "app.services.food_service._fetch_from_ai",
            new_callable=AsyncMock,
        )
        r = await client.get(
            f"{BASE}/foods/macros",
            params={"name": "stale food", "weight": 100},
            headers=auth_headers,
        )
        assert r.status_code == 200
        # Expected: 10*4 + 5*4 + 4*9 = 40 + 20 + 36 = 96 kcal per 100g → for 100g = 96 kcal
        assert r.json()["calories_kcal"] == pytest.approx(96.0, abs=0.1)

    async def test_food_saved_to_db_after_ai_call(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """After AI lookup, food appears in GET /foods/search."""
        _mock_full_ai(mocker)
        await client.get(
            f"{BASE}/foods/macros",
            params={"name": "broccoli", "weight": 100},
            headers=auth_headers,
        )
        r = await client.get(f"{BASE}/foods/search", params={"q": "broccoli"})
        assert len(r.json()["results"]) == 1
        assert r.json()["results"][0]["name"] == "broccoli"

    async def test_requires_auth(self, client: AsyncClient):
        """Returns 403 without Authorization header."""
        r = await client.get(
            f"{BASE}/foods/macros", params={"name": "apple", "weight": 100}
        )
        assert r.status_code == 403

    async def test_weight_zero_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ):
        """weight=0 fails validation."""
        r = await client.get(
            f"{BASE}/foods/macros",
            params={"name": "apple", "weight": 0},
            headers=auth_headers,
        )
        assert r.status_code == 422

    async def test_ai_invalid_json_returns_502(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """When AI returns unparseable data, endpoint returns 502."""
        mocker.patch(
            "app.services.food_service._fetch_from_ai",
            new_callable=AsyncMock,
            side_effect=AppError(502, "AI returned unparseable data", "AI_PARSE_ERROR"),
        )
        r = await client.get(
            f"{BASE}/foods/macros",
            params={"name": "unknown food xyz", "weight": 100},
            headers=auth_headers,
        )
        assert r.status_code == 502

    async def test_response_contains_food_object(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mocker
    ):
        """Response body includes nested food object with per-100g values."""
        await _seed_food(db_session, name="tuna")
        mocker.patch("app.services.food_service._fetch_from_ai", new_callable=AsyncMock)
        r = await client.get(
            f"{BASE}/foods/macros",
            params={"name": "tuna", "weight": 100},
            headers=auth_headers,
        )
        body = r.json()
        assert "food" in body
        assert body["food"]["name"] == "tuna"
        assert "calories_per_100g" in body["food"]


# ---------------------------------------------------------------------------
# POST /foods/complete
# ---------------------------------------------------------------------------


class TestFoodComplete:
    """POST /foods/complete — completes partial macros via AI or formula."""

    async def test_one_bju_known_calls_ai(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """1 known BJ/U field → AI called to fill the other 2."""
        mock = _mock_partial_ai(mocker, {"protein_per_100g": 18.0, "carbs_per_100g": 3.0})
        r = await client.post(
            f"{BASE}/foods/complete",
            json={"name": "cottage cheese", "weight_g": 200.0, "known": {"fat_per_100g": 9.0}},
            headers=auth_headers,
        )
        assert r.status_code == 200
        mock.assert_called_once()
        body = r.json()
        assert body["fat_g"] > 0
        assert body["protein_g"] > 0
        assert body["calories_kcal"] > 0

    async def test_two_bju_known_calls_ai_for_missing_one(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """2 known BJ/U fields → AI called for the 1 missing field."""
        mock = _mock_partial_ai(mocker, {"carbs_per_100g": 3.0})
        r = await client.post(
            f"{BASE}/foods/complete",
            json={
                "name": "cottage cheese",
                "weight_g": 200.0,
                "known": {"fat_per_100g": 9.0, "protein_per_100g": 18.0},
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        mock.assert_called_once()

    async def test_all_bju_known_no_ai_call(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """All 3 BJ/U known → AI never called, calories = P×4 + C×4 + F×9."""
        mock = _mock_partial_ai(mocker)
        r = await client.post(
            f"{BASE}/foods/complete",
            json={
                "name": "greek yogurt",
                "weight_g": 150.0,
                "known": {
                    "protein_per_100g": 10.0,
                    "carbs_per_100g": 4.0,
                    "fat_per_100g": 0.4,
                },
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        mock.assert_not_called()
        # calories_per_100g = 10*4 + 4*4 + 0.4*9 = 40+16+3.6 = 59.6 → for 150g = 89.4
        assert r.json()["calories_kcal"] == pytest.approx(89.4, abs=0.5)

    async def test_calories_calculated_by_formula(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """Calories in response match Atwater formula regardless of AI."""
        _mock_partial_ai(mocker, {"protein_per_100g": 20.0, "carbs_per_100g": 5.0})
        r = await client.post(
            f"{BASE}/foods/complete",
            json={"name": "mystery food", "weight_g": 100.0, "known": {"fat_per_100g": 10.0}},
            headers=auth_headers,
        )
        body = r.json()
        # For 100g: protein=20, carbs=5, fat=10 → 20*4+5*4+10*9 = 80+20+90 = 190
        assert body["calories_kcal"] == pytest.approx(190.0, abs=0.5)

    async def test_upsert_updates_existing_record(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mocker
    ):
        """Calling complete on existing food name updates DB values."""
        await _seed_food(db_session, name="cream cheese", fat=10.0, protein=7.0, carbs=4.0, calories=170.0)
        _mock_partial_ai(mocker, {"protein_per_100g": 8.0, "carbs_per_100g": 2.0})
        r = await client.post(
            f"{BASE}/foods/complete",
            json={"name": "cream cheese", "weight_g": 100.0, "known": {"fat_per_100g": 33.0}},
            headers=auth_headers,
        )
        assert r.status_code == 200
        # fat updated to 33g per 100g
        assert r.json()["fat_g"] == pytest.approx(33.0, abs=0.5)

    async def test_food_saved_to_db_after_complete(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """After POST /foods/complete, food is findable via GET /foods/search."""
        _mock_partial_ai(mocker, {"protein_per_100g": 5.0, "carbs_per_100g": 2.0})
        await client.post(
            f"{BASE}/foods/complete",
            json={"name": "kefir", "weight_g": 250.0, "known": {"fat_per_100g": 3.2}},
            headers=auth_headers,
        )
        r = await client.get(f"{BASE}/foods/search", params={"q": "kefir"})
        assert len(r.json()["results"]) == 1

    async def test_requires_auth(self, client: AsyncClient):
        """Returns 403 without Authorization header."""
        r = await client.post(
            f"{BASE}/foods/complete",
            json={"name": "yogurt", "weight_g": 100.0, "known": {"fat_per_100g": 5.0}},
        )
        assert r.status_code == 403

    async def test_weight_zero_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ):
        """weight_g=0 fails Pydantic validation."""
        r = await client.post(
            f"{BASE}/foods/complete",
            json={"name": "yogurt", "weight_g": 0, "known": {"fat_per_100g": 5.0}},
            headers=auth_headers,
        )
        assert r.status_code == 422

    async def test_empty_known_calls_full_ai_path(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """known={} means all BJ/U are missing → AI fills all 3 fields."""
        mock = _mock_partial_ai(
            mocker, {"protein_per_100g": 5.0, "carbs_per_100g": 12.0, "fat_per_100g": 1.0}
        )
        r = await client.post(
            f"{BASE}/foods/complete",
            json={"name": "peach", "weight_g": 100.0, "known": {}},
            headers=auth_headers,
        )
        assert r.status_code == 200
        mock.assert_called_once()

    async def test_response_weight_matches_request(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """Response weight_g equals the requested weight."""
        _mock_partial_ai(mocker, {"protein_per_100g": 3.0, "carbs_per_100g": 1.0})
        r = await client.post(
            f"{BASE}/foods/complete",
            json={"name": "butter", "weight_g": 20.0, "known": {"fat_per_100g": 82.0}},
            headers=auth_headers,
        )
        assert r.json()["weight_g"] == 20.0


# ---------------------------------------------------------------------------
# Service unit tests (async: _upsert_food requires DB session)
# Sync helpers (_calc_calories, _calculate_macros, _build_completion_prompt)
# are tested without DB in tests/test_food_unit.py
# ---------------------------------------------------------------------------


class TestUpsertFood:
    """Unit tests for _upsert_food (insert vs update)."""

    async def test_creates_new_record(self, db_session: AsyncSession):
        """Food not in DB → new row is inserted."""
        macros = {"calories_per_100g": 52.0, "protein_per_100g": 0.3, "carbs_per_100g": 14.0, "fat_per_100g": 0.2}
        food = await _upsert_food(db_session, "apple", macros)
        assert food.id is not None
        assert food.name == "apple"
        assert food.caloriesPer100g == 52.0

    async def test_updates_existing_record(self, db_session: AsyncSession):
        """Food already in DB → existing row is updated, not duplicated."""
        await _seed_food(db_session, name="banana", calories=89.0, protein=1.1, carbs=23.0, fat=0.3)
        new_macros = {"calories_per_100g": 95.0, "protein_per_100g": 1.3, "carbs_per_100g": 24.0, "fat_per_100g": 0.4}
        food = await _upsert_food(db_session, "banana", new_macros)
        assert food.caloriesPer100g == 95.0
        assert food.proteinPer100g == 1.3

    async def test_upsert_does_not_create_duplicate(self, db_session: AsyncSession):
        """Calling upsert twice for same name results in exactly 1 row."""
        from sqlalchemy import func, select
        from app.models.food import Food as FoodModel

        macros = {"calories_per_100g": 52.0, "protein_per_100g": 0.3, "carbs_per_100g": 14.0, "fat_per_100g": 0.2}
        await _upsert_food(db_session, "pear", macros)
        macros["calories_per_100g"] = 55.0
        await _upsert_food(db_session, "pear", macros)

        result = await db_session.execute(
            select(func.count()).where(FoodModel.name == "pear")
        )
        assert result.scalar() == 1


