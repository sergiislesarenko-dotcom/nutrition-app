"""
Pure sync unit tests for food service helpers.
No DB, no event loop — kept in a separate file to avoid asyncio pytestmark warnings.
"""
import pytest

from app.models.food import Food
from app.services.food_service import (
    _build_completion_prompt,
    _calc_calories,
    _calculate_macros,
)


class TestCalcCalories:
    """Unit tests for _calc_calories (Atwater formula)."""

    def test_standard_values(self):
        """Protein=10, carbs=5, fat=4 → 10*4 + 5*4 + 4*9 = 96 kcal."""
        assert _calc_calories(10.0, 5.0, 4.0) == pytest.approx(96.0, abs=0.01)

    def test_all_zeros(self):
        """Zero macros → 0 calories."""
        assert _calc_calories(0.0, 0.0, 0.0) == 0.0

    def test_fat_heavy(self):
        """High-fat food: fat=82, protein=0.5, carbs=0.5."""
        expected = 0.5 * 4 + 0.5 * 4 + 82.0 * 9
        assert _calc_calories(0.5, 0.5, 82.0) == pytest.approx(expected, abs=0.1)

    def test_rounded_to_one_decimal(self):
        """Result is rounded to 1 decimal place."""
        result = _calc_calories(1.0, 1.0, 1.0)
        assert result == round(result, 1)


class TestCalculateMacros:
    """Unit tests for _calculate_macros — scaling and calories=0 fallback.

    Food constructed in-memory with id=1 to satisfy FoodOut's non-nullable id.
    """

    def test_normal_scaling(self):
        """Per-100g values scaled correctly to requested weight."""
        food = Food(id=1, name="test", caloriesPer100g=100.0, proteinPer100g=10.0,
                    carbsPer100g=5.0, fatPer100g=4.0)
        result = _calculate_macros(food, 200.0)
        assert result.caloriesKcal == pytest.approx(200.0, abs=0.1)
        assert result.proteinG == pytest.approx(20.0, abs=0.1)
        assert result.carbsG == pytest.approx(10.0, abs=0.1)
        assert result.fatG == pytest.approx(8.0, abs=0.1)

    def test_calories_zero_with_nonzero_bju_uses_formula(self):
        """calories_per_100g=0 + non-zero BJ/U → Atwater formula kicks in."""
        food = Food(id=1, name="test", caloriesPer100g=0.0, proteinPer100g=10.0,
                    carbsPer100g=5.0, fatPer100g=4.0)
        result = _calculate_macros(food, 100.0)
        # 10*4 + 5*4 + 4*9 = 96
        assert result.caloriesKcal == pytest.approx(96.0, abs=0.1)

    def test_all_zeros_stays_zero(self):
        """calories=0 + all BJ/U=0 → calories remains 0."""
        food = Food(id=1, name="water", caloriesPer100g=0.0, proteinPer100g=0.0,
                    carbsPer100g=0.0, fatPer100g=0.0)
        assert _calculate_macros(food, 500.0).caloriesKcal == 0.0


class TestBuildCompletionPrompt:
    """Unit tests for _build_completion_prompt."""

    def test_contains_food_name(self):
        """Food name is present in the generated prompt."""
        prompt = _build_completion_prompt(
            "cottage cheese", {"fat_per_100g": 9.0}, {"protein_per_100g", "carbs_per_100g"}
        )
        assert "cottage cheese" in prompt

    def test_known_value_appears_in_prompt(self):
        """Known fat value is visible in the prompt."""
        prompt = _build_completion_prompt(
            "tuna", {"fat_per_100g": 1.0}, {"protein_per_100g", "carbs_per_100g"}
        )
        assert "fat" in prompt
        assert "1.0" in prompt

    def test_missing_key_in_json_template(self):
        """Missing field name appears in the JSON format section."""
        prompt = _build_completion_prompt("egg", {"fat_per_100g": 10.0}, {"protein_per_100g"})
        assert "protein_per_100g" in prompt

    def test_known_key_not_in_missing_json_template(self):
        """Known (fat) field does not appear in the missing-fields JSON template."""
        prompt = _build_completion_prompt("egg", {"fat_per_100g": 10.0}, {"protein_per_100g"})
        lines = prompt.splitlines()
        json_line = next((l for l in lines if "Return ONLY valid JSON" in l), "")
        assert "fat_per_100g" not in json_line
