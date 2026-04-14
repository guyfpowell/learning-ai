from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from clients.base import ModelOutputError
from models.schemas import CoachingOutput


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

VALID_COACHING = {
    "message": "Great question! Python variables store data of any type.",
    "suggestions": ["Try declaring your own variable!", "What type would a name be?"],
}

COACHING_REQUEST = {
    "messages": [{"role": "user", "content": "What is a variable?"}],
    "lesson_context": "This lesson covers Python variables and data types.",
    "user_context": {"goal": "learn Python", "skill_level": "beginner"},
    "tier": "pro",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_api_key(monkeypatch):
    monkeypatch.setenv("AI_SERVICE_API_KEY", "test-key-abc")
    return "test-key-abc"


@pytest.fixture
async def client(valid_api_key):
    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_client_returning_coaching():
    mock = MagicMock()
    mock.coaching_reply = AsyncMock(return_value=CoachingOutput(**VALID_COACHING))
    return mock


def _mock_client_raising(error_msg: str):
    mock = MagicMock()
    mock.coaching_reply = AsyncMock(side_effect=ModelOutputError(error_msg))
    return mock


# ---------------------------------------------------------------------------
# POST /coaching/message
# ---------------------------------------------------------------------------


class TestCoachingMessageEndpoint:
    async def test_returns_coaching_output(self, client, valid_api_key):
        mock = _mock_client_returning_coaching()
        with patch("routers.coaching.get_model_client", return_value=mock):
            response = await client.post(
                "/coaching/message",
                json=COACHING_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "Great question! Python variables store data of any type."
        assert len(body["suggestions"]) == 2

    async def test_passes_lesson_context_in_system_message(self, client, valid_api_key):
        mock = _mock_client_returning_coaching()
        with patch("routers.coaching.get_model_client", return_value=mock):
            await client.post(
                "/coaching/message",
                json=COACHING_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        mock.coaching_reply.assert_called_once()
        messages = mock.coaching_reply.call_args[0][0]
        system_message = messages[0]
        assert system_message["role"] == "system"
        assert "Python variables and data types." in system_message["content"]

    async def test_passes_conversation_history(self, client, valid_api_key):
        mock = _mock_client_returning_coaching()
        with patch("routers.coaching.get_model_client", return_value=mock):
            await client.post(
                "/coaching/message",
                json=COACHING_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        mock.coaching_reply.assert_called_once()
        messages = mock.coaching_reply.call_args[0][0]
        # system message is prepended — user message is second
        assert len(messages) == 2
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "What is a variable?"

    async def test_injects_user_goal_in_system_message(self, client, valid_api_key):
        mock = _mock_client_returning_coaching()
        with patch("routers.coaching.get_model_client", return_value=mock):
            await client.post(
                "/coaching/message",
                json=COACHING_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        messages = mock.coaching_reply.call_args[0][0]
        assert "learn Python" in messages[0]["content"]

    async def test_returns_502_on_model_output_error(self, client, valid_api_key):
        mock = _mock_client_raising("Coaching output validation failed")
        with patch("routers.coaching.get_model_client", return_value=mock):
            response = await client.post(
                "/coaching/message",
                json=COACHING_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        assert response.status_code == 502
        assert "Coaching output validation failed" in response.json()["detail"]

    async def test_returns_401_without_api_key(self, client):
        response = await client.post("/coaching/message", json=COACHING_REQUEST)
        assert response.status_code == 401
