from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from clients.base import ModelOutputError
from models.schemas import LessonOutput, QuizOutput


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

VALID_LESSON = {
    "title": "Introduction to Python",
    "content": "Python is an interpreted, high-level programming language.",
    "estimated_minutes": 3,
    "key_takeaways": ["Easy to read", "Versatile", "Large ecosystem"],
    "quiz": {
        "question": "What type of language is Python?",
        "options": ["Interpreted", "Compiled", "Assembly", "Markup"],
        "correct_answer": "Interpreted",
        "explanation": "Python is interpreted at runtime.",
    },
}

VALID_QUIZ = {
    "question": "What type of language is Python?",
    "options": ["Interpreted", "Compiled", "Assembly", "Markup"],
    "correct_answer": "Interpreted",
    "explanation": "Python is interpreted at runtime.",
}

LESSON_REQUEST = {
    "skill_id": "python-basics",
    "skill_level": "beginner",
    "topic": "Python variables",
    "user_context": {
        "goal": "learn Python",
        "learning_style": "visual",
        "completed_lessons": 0,
    },
    "tier": "free",
}

QUIZ_REQUEST = {
    "lesson_content": "Python uses variables to store data.",
    "skill_level": "beginner",
    "tier": "free",
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


def _mock_client_returning_lesson():
    mock = MagicMock()
    mock.generate_lesson = AsyncMock(return_value=LessonOutput(**VALID_LESSON))
    return mock


def _mock_client_returning_quiz():
    mock = MagicMock()
    mock.generate_quiz = AsyncMock(return_value=QuizOutput(**VALID_QUIZ))
    return mock


def _mock_client_raising(method: str, error_msg: str):
    mock = MagicMock()
    setattr(mock, method, AsyncMock(side_effect=ModelOutputError(error_msg)))
    return mock


# ---------------------------------------------------------------------------
# POST /generate/lesson
# ---------------------------------------------------------------------------


class TestGenerateLessonEndpoint:
    async def test_returns_lesson_output(self, client, valid_api_key):
        mock = _mock_client_returning_lesson()
        with patch("routers.generate.get_model_client", return_value=mock):
            response = await client.post(
                "/generate/lesson",
                json=LESSON_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Introduction to Python"
        assert body["estimated_minutes"] == 3
        assert len(body["key_takeaways"]) == 3

    async def test_passes_topic_and_level_in_prompt(self, client, valid_api_key):
        mock = _mock_client_returning_lesson()
        with patch("routers.generate.get_model_client", return_value=mock):
            await client.post(
                "/generate/lesson",
                json=LESSON_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        mock.generate_lesson.assert_called_once()
        prompt_arg = mock.generate_lesson.call_args[0][0]
        assert "Python variables" in prompt_arg
        assert "beginner" in prompt_arg

    async def test_returns_502_on_model_output_error(self, client, valid_api_key):
        mock = _mock_client_raising("generate_lesson", "Lesson output validation failed")
        with patch("routers.generate.get_model_client", return_value=mock):
            response = await client.post(
                "/generate/lesson",
                json=LESSON_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        assert response.status_code == 502
        assert "Lesson output validation failed" in response.json()["detail"]

    async def test_returns_401_without_api_key(self, client):
        response = await client.post("/generate/lesson", json=LESSON_REQUEST)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /generate/quiz
# ---------------------------------------------------------------------------


class TestGenerateQuizEndpoint:
    async def test_returns_quiz_output(self, client, valid_api_key):
        mock = _mock_client_returning_quiz()
        with patch("routers.generate.get_model_client", return_value=mock):
            response = await client.post(
                "/generate/quiz",
                json=QUIZ_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["question"] == "What type of language is Python?"
        assert len(body["options"]) == 4

    async def test_passes_lesson_content_in_prompt(self, client, valid_api_key):
        mock = _mock_client_returning_quiz()
        with patch("routers.generate.get_model_client", return_value=mock):
            await client.post(
                "/generate/quiz",
                json=QUIZ_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        mock.generate_quiz.assert_called_once()
        prompt_arg = mock.generate_quiz.call_args[0][0]
        assert "Python uses variables to store data." in prompt_arg

    async def test_returns_502_on_model_output_error(self, client, valid_api_key):
        mock = _mock_client_raising("generate_quiz", "Quiz output validation failed")
        with patch("routers.generate.get_model_client", return_value=mock):
            response = await client.post(
                "/generate/quiz",
                json=QUIZ_REQUEST,
                headers={"X-Internal-API-Key": valid_api_key},
            )
        assert response.status_code == 502
        assert "Quiz output validation failed" in response.json()["detail"]

    async def test_returns_401_without_api_key(self, client):
        response = await client.post("/generate/quiz", json=QUIZ_REQUEST)
        assert response.status_code == 401
