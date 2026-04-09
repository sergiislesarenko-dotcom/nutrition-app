from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")

BASE = "/api/v1"


def _mock_chat_response(mocker, text: str = "Eat more protein."):
    """Patch _make_client to return a mock that returns a chat response."""
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_msg)
    mocker.patch("app.services.ai_service._make_client", return_value=mock_client)
    return text


def _mock_stream_response(mocker, chunks: list[str] | None = None):
    """Patch _make_client to return a mock that streams chunks via SSE."""
    chunks = chunks or ["Hello ", "world!"]

    async def _text_stream():
        for chunk in chunks:
            yield chunk

    mock_stream = MagicMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=None)
    mock_stream.text_stream = _text_stream()

    # messages.stream() must be a sync call returning the context manager object
    mock_client = MagicMock()
    mock_client.messages.stream.return_value = mock_stream
    mocker.patch("app.services.ai_service._make_client", return_value=mock_client)
    return chunks


class TestChat:
    """POST /ai/chat"""

    async def test_chat_success(self, client: AsyncClient, auth_headers: dict, mocker):
        """Returns answer and recommendation_id; stores in DB."""
        expected = _mock_chat_response(mocker, "Increase your protein intake.")
        response = await client.post(
            f"{BASE}/ai/chat",
            json={"message": "How can I improve my diet?"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == expected
        assert isinstance(body["recommendation_id"], int)

    async def test_chat_requires_auth(self, client: AsyncClient, mocker):
        """Returns 403 without a token."""
        _mock_chat_response(mocker)
        response = await client.post(
            f"{BASE}/ai/chat", json={"message": "Hello"}
        )
        assert response.status_code == 403

    async def test_chat_empty_message(self, client: AsyncClient, auth_headers: dict, mocker):
        """Returns 422 for an empty message."""
        _mock_chat_response(mocker)
        response = await client.post(
            f"{BASE}/ai/chat", json={"message": ""}, headers=auth_headers
        )
        assert response.status_code == 422

    async def test_chat_stored_in_recommendations(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """After a chat call, recommendation appears in GET /ai/recommendations."""
        _mock_chat_response(mocker, "Drink more water.")
        await client.post(
            f"{BASE}/ai/chat",
            json={"message": "What should I drink?"},
            headers=auth_headers,
        )
        rec_response = await client.get(
            f"{BASE}/ai/recommendations", headers=auth_headers
        )
        assert rec_response.status_code == 200
        body = rec_response.json()
        assert body["total"] == 1
        assert body["items"][0]["answer"] == "Drink more water."
        assert body["items"][0]["question"] == "What should I drink?"


class TestChatStream:
    """POST /ai/chat/stream"""

    async def test_stream_returns_sse(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """Returns text/event-stream with data chunks and [DONE]."""
        chunks = _mock_stream_response(mocker, ["Hello ", "world!"])
        response = await client.post(
            f"{BASE}/ai/chat/stream",
            json={"message": "Tell me something"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        text = response.text
        for chunk in chunks:
            assert f"data: {chunk}" in text
        assert "data: [DONE]" in text

    async def test_stream_stores_recommendation(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """After streaming, the full answer is stored in recommendations."""
        _mock_stream_response(mocker, ["Eat ", "greens!"])
        await client.post(
            f"{BASE}/ai/chat/stream",
            json={"message": "What to eat?"},
            headers=auth_headers,
        )
        rec_resp = await client.get(f"{BASE}/ai/recommendations", headers=auth_headers)
        assert rec_resp.json()["items"][0]["answer"] == "Eat greens!"


class TestRecommendations:
    """GET /ai/recommendations"""

    async def test_recommendations_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Returns empty list when no chats have occurred."""
        response = await client.get(
            f"{BASE}/ai/recommendations", headers=auth_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["items"] == []

    async def test_recommendations_pagination(
        self, client: AsyncClient, auth_headers: dict, mocker
    ):
        """limit and offset params are respected."""
        for i in range(3):
            _mock_chat_response(mocker, f"Answer {i}")
            await client.post(
                f"{BASE}/ai/chat",
                json={"message": f"Question {i}"},
                headers=auth_headers,
            )
        response = await client.get(
            f"{BASE}/ai/recommendations?limit=2&offset=0", headers=auth_headers
        )
        body = response.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2


class TestRestrictions:
    """POST / GET / DELETE /users/me/restrictions"""

    async def test_add_restriction_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Returns 201 with the created restriction."""
        response = await client.post(
            f"{BASE}/users/me/restrictions",
            json={"type": "allergy", "value": "peanuts"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["type"] == "allergy"
        assert body["value"] == "peanuts"
        assert "id" in body

    async def test_get_restrictions_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Returns empty list when no restrictions added."""
        response = await client.get(
            f"{BASE}/users/me/restrictions", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_restrictions_after_add(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Added restriction appears in GET list."""
        await client.post(
            f"{BASE}/users/me/restrictions",
            json={"type": "dietary", "value": "vegan"},
            headers=auth_headers,
        )
        response = await client.get(
            f"{BASE}/users/me/restrictions", headers=auth_headers
        )
        assert len(response.json()) == 1
        assert response.json()[0]["value"] == "vegan"

    async def test_delete_restriction_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Restriction is removed after DELETE."""
        add_r = await client.post(
            f"{BASE}/users/me/restrictions",
            json={"type": "medical", "value": "lactose intolerance"},
            headers=auth_headers,
        )
        rid = add_r.json()["id"]
        del_r = await client.delete(
            f"{BASE}/users/me/restrictions/{rid}", headers=auth_headers
        )
        assert del_r.status_code == 204
        get_r = await client.get(
            f"{BASE}/users/me/restrictions", headers=auth_headers
        )
        assert get_r.json() == []

    async def test_add_restriction_invalid_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Returns 422 for an unknown restriction type."""
        response = await client.post(
            f"{BASE}/users/me/restrictions",
            json={"type": "lifestyle", "value": "keto"},
            headers=auth_headers,
        )
        assert response.status_code == 422
