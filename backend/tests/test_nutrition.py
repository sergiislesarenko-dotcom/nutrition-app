import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")

BASE = "/api/v1"


class TestNutritionLogs:
    """POST / GET / DELETE /nutrition/logs"""

    async def test_create_log_success(
        self, client: AsyncClient, auth_headers: dict, log_payload: dict
    ):
        """Returns 201 with all log fields present."""
        response = await client.post(
            f"{BASE}/nutrition/logs", json=log_payload, headers=auth_headers
        )
        assert response.status_code == 201
        body = response.json()
        assert body["food_name"] == log_payload["food_name"]
        assert body["meal_type"] == log_payload["meal_type"]
        assert body["calories_kcal"] == log_payload["calories_kcal"]
        assert "id" in body
        assert "logged_at" in body

    async def test_create_log_invalid_meal_type(
        self, client: AsyncClient, auth_headers: dict, log_payload: dict
    ):
        """Returns 422 for an unknown meal type."""
        log_payload["meal_type"] = "brunch"
        response = await client.post(
            f"{BASE}/nutrition/logs", json=log_payload, headers=auth_headers
        )
        assert response.status_code == 422

    async def test_create_log_requires_auth(
        self, client: AsyncClient, log_payload: dict
    ):
        """Returns 403 without an auth token."""
        response = await client.post(f"{BASE}/nutrition/logs", json=log_payload)
        assert response.status_code == 403

    async def test_get_logs_empty(self, client: AsyncClient, auth_headers: dict):
        """Returns 200 with empty list and zero summary when no logs exist."""
        response = await client.get(f"{BASE}/nutrition/logs", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["logs"] == []
        assert body["summary"]["total_calories"] == 0.0
        assert body["summary"]["goal_calories"] is None
        assert body["summary"]["deficit_surplus"] is None

    async def test_get_logs_returns_created_log(
        self, client: AsyncClient, auth_headers: dict, log_payload: dict
    ):
        """Created log appears in GET /nutrition/logs for today."""
        await client.post(
            f"{BASE}/nutrition/logs", json=log_payload, headers=auth_headers
        )
        response = await client.get(f"{BASE}/nutrition/logs", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert len(body["logs"]) == 1
        assert body["summary"]["total_calories"] == log_payload["calories_kcal"]
        assert body["summary"]["total_protein"] == log_payload["protein_g"]

    async def test_get_logs_date_filter(
        self, client: AsyncClient, auth_headers: dict, log_payload: dict
    ):
        """Logs on a different date are excluded by the date filter."""
        await client.post(
            f"{BASE}/nutrition/logs", json=log_payload, headers=auth_headers
        )
        response = await client.get(
            f"{BASE}/nutrition/logs?date=2020-01-01", headers=auth_headers
        )
        assert response.json()["logs"] == []

    async def test_get_logs_days_param(
        self, client: AsyncClient, auth_headers: dict, log_payload: dict
    ):
        """days=7 still returns today's log."""
        await client.post(
            f"{BASE}/nutrition/logs", json=log_payload, headers=auth_headers
        )
        response = await client.get(
            f"{BASE}/nutrition/logs?days=7", headers=auth_headers
        )
        assert len(response.json()["logs"]) == 1

    async def test_delete_log_success(
        self, client: AsyncClient, auth_headers: dict, log_payload: dict
    ):
        """Returns 204 and log no longer appears in GET."""
        create_r = await client.post(
            f"{BASE}/nutrition/logs", json=log_payload, headers=auth_headers
        )
        log_id = create_r.json()["id"]
        delete_r = await client.delete(
            f"{BASE}/nutrition/logs/{log_id}", headers=auth_headers
        )
        assert delete_r.status_code == 204
        get_r = await client.get(f"{BASE}/nutrition/logs", headers=auth_headers)
        assert get_r.json()["logs"] == []

    async def test_delete_log_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Returns 404 for a non-existent log id."""
        response = await client.delete(
            f"{BASE}/nutrition/logs/99999", headers=auth_headers
        )
        assert response.status_code == 404
        assert response.json()["code"] == "LOG_NOT_FOUND"


class TestGoals:
    """POST /goals, GET /goals/active"""

    async def test_get_active_goal_none(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Returns null when no goal has been set."""
        response = await client.get(f"{BASE}/goals/active", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() is None

    async def test_create_goal_success(
        self, client: AsyncClient, auth_headers: dict, goal_payload: dict
    ):
        """Returns 201 with is_active=True and correct fields."""
        response = await client.post(
            f"{BASE}/goals", json=goal_payload, headers=auth_headers
        )
        assert response.status_code == 201
        body = response.json()
        assert body["goal_type"] == goal_payload["goal_type"]
        assert body["daily_calories_kcal"] == goal_payload["daily_calories_kcal"]
        assert body["is_active"] is True

    async def test_get_active_goal_after_create(
        self, client: AsyncClient, auth_headers: dict, goal_payload: dict
    ):
        """GET /goals/active returns the newly created goal."""
        await client.post(f"{BASE}/goals", json=goal_payload, headers=auth_headers)
        response = await client.get(f"{BASE}/goals/active", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["goal_type"] == goal_payload["goal_type"]

    async def test_new_goal_deactivates_previous(
        self, client: AsyncClient, auth_headers: dict, goal_payload: dict
    ):
        """Creating a second goal deactivates the first; only one active exists."""
        await client.post(f"{BASE}/goals", json=goal_payload, headers=auth_headers)
        goal_payload["goal_type"] = "muscle_gain"
        await client.post(f"{BASE}/goals", json=goal_payload, headers=auth_headers)
        response = await client.get(f"{BASE}/goals/active", headers=auth_headers)
        assert response.json()["goal_type"] == "muscle_gain"

    async def test_logs_summary_reflects_goal(
        self, client: AsyncClient, auth_headers: dict, goal_payload: dict, log_payload: dict
    ):
        """DaySummary includes goal_calories and deficit_surplus when goal is set."""
        await client.post(f"{BASE}/goals", json=goal_payload, headers=auth_headers)
        await client.post(
            f"{BASE}/nutrition/logs", json=log_payload, headers=auth_headers
        )
        response = await client.get(f"{BASE}/nutrition/logs", headers=auth_headers)
        summary = response.json()["summary"]
        assert summary["goal_calories"] == goal_payload["daily_calories_kcal"]
        expected_deficit = log_payload["calories_kcal"] - goal_payload["daily_calories_kcal"]
        assert summary["deficit_surplus"] == pytest.approx(expected_deficit)

    async def test_create_goal_invalid_type(
        self, client: AsyncClient, auth_headers: dict, goal_payload: dict
    ):
        """Returns 422 for an unknown goal type."""
        goal_payload["goal_type"] = "immortality"
        response = await client.post(
            f"{BASE}/goals", json=goal_payload, headers=auth_headers
        )
        assert response.status_code == 422
