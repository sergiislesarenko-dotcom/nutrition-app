import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")

BASE = "/api/v1"


class TestRegister:
    """POST /auth/register"""

    async def test_register_success(self, client: AsyncClient, user_payload: dict):
        """Returns 201 with user profile and access token."""
        response = await client.post(f"{BASE}/auth/register", json=user_payload)
        assert response.status_code == 201
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        user = body["user"]
        assert user["email"] == user_payload["email"]
        assert user["age"] == user_payload["age"]
        assert "bmi" in user
        assert "tdee" in user
        assert "password" not in user

    async def test_register_duplicate_email(self, client: AsyncClient, user_payload: dict):
        """Returns 409 when email is already registered."""
        await client.post(f"{BASE}/auth/register", json=user_payload)
        response = await client.post(f"{BASE}/auth/register", json=user_payload)
        assert response.status_code == 409
        body = response.json()
        assert body["code"] == "EMAIL_EXISTS"

    async def test_register_invalid_data(self, client: AsyncClient, user_payload: dict):
        """Returns 422 on validation failure (bad activity_level)."""
        user_payload["activity_level"] = "couch_potato"
        response = await client.post(f"{BASE}/auth/register", json=user_payload)
        assert response.status_code == 422

    async def test_register_missing_field(self, client: AsyncClient, user_payload: dict):
        """Returns 422 when a required field is absent."""
        del user_payload["email"]
        response = await client.post(f"{BASE}/auth/register", json=user_payload)
        assert response.status_code == 422


class TestLogin:
    """POST /auth/login"""

    async def test_login_success(self, client: AsyncClient, registered_user: dict, user_payload: dict):
        """Returns 200 with access token for valid credentials."""
        response = await client.post(
            f"{BASE}/auth/login",
            json={"email": user_payload["email"], "password": user_payload["password"]},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, registered_user: dict, user_payload: dict):
        """Returns 401 with AUTH_FAILED code on wrong password."""
        response = await client.post(
            f"{BASE}/auth/login",
            json={"email": user_payload["email"], "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "AUTH_FAILED"

    async def test_login_unknown_email(self, client: AsyncClient):
        """Returns 401 for an email that was never registered."""
        response = await client.post(
            f"{BASE}/auth/login",
            json={"email": "nobody@example.com", "password": "irrelevant"},
        )
        assert response.status_code == 401


class TestGetMe:
    """GET /users/me"""

    async def test_get_me_success(self, client: AsyncClient, auth_headers: dict, user_payload: dict):
        """Returns 200 with the authenticated user's profile."""
        response = await client.get(f"{BASE}/users/me", headers=auth_headers)
        assert response.status_code == 200
        user = response.json()
        assert user["email"] == user_payload["email"]
        assert isinstance(user["bmi"], float)
        assert isinstance(user["tdee"], int)

    async def test_get_me_no_token(self, client: AsyncClient):
        """Returns 403 when no Authorization header is present."""
        response = await client.get(f"{BASE}/users/me")
        assert response.status_code == 403

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Returns 403 when the token is malformed."""
        response = await client.get(
            f"{BASE}/users/me", headers={"Authorization": "Bearer notavalidtoken"}
        )
        assert response.status_code == 401


class TestUpdateMe:
    """PATCH /users/me"""

    async def test_update_me_success(self, client: AsyncClient, auth_headers: dict):
        """Returns 200 with updated profile values."""
        response = await client.patch(
            f"{BASE}/users/me",
            json={"weight_kg": 75.0, "age": 26},
            headers=auth_headers,
        )
        assert response.status_code == 200
        user = response.json()
        assert user["weight_kg"] == 75.0
        assert user["age"] == 26

    async def test_update_me_recalculates_bmi(self, client: AsyncClient, auth_headers: dict):
        """BMI is recomputed after a weight update."""
        r1 = await client.get(f"{BASE}/users/me", headers=auth_headers)
        original_bmi = r1.json()["bmi"]

        await client.patch(
            f"{BASE}/users/me", json={"weight_kg": 90.0}, headers=auth_headers
        )
        r2 = await client.get(f"{BASE}/users/me", headers=auth_headers)
        assert r2.json()["bmi"] != original_bmi

    async def test_update_me_invalid_gender(self, client: AsyncClient, auth_headers: dict):
        """Returns 422 for an invalid gender value."""
        response = await client.patch(
            f"{BASE}/users/me", json={"gender": "robot"}, headers=auth_headers
        )
        assert response.status_code == 422
