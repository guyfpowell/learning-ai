import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from clients.base import ModelOutputError
from clients.ollama_client import OllamaClient
from clients.vertex_client import VertexClient
from clients import get_model_client
from models.schemas import CoachingOutput, LessonOutput, QuizOutput


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

VALID_LESSON = {
    "title": "Introduction to Python",
    "content": "Python is an interpreted, high-level programming language.",
    "estimated_minutes": 3,
    "key_takeaways": ["Easy to read", "Versatile"],
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

VALID_COACHING = {
    "message": "Great question! Python's indentation enforces code structure.",
    "suggestions": ["Try the REPL", "Read PEP 8"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_httpx_client(response_json: dict) -> MagicMock:
    """Return a mock httpx.AsyncClient context manager that yields response_json."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = response_json

    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    return mock_cm


def _mock_vertex_model(response_text: str) -> MagicMock:
    """Return a mock GenerativeModel whose generate_content_async returns response_text."""
    mock_response = MagicMock()
    mock_response.text = response_text

    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    return mock_model


# ---------------------------------------------------------------------------
# OllamaClient
# ---------------------------------------------------------------------------

class TestOllamaClient:
    async def test_generate_lesson_returns_lesson_output(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "llama3:8b")

        mock_cm = _mock_httpx_client({"response": json.dumps(VALID_LESSON)})
        with patch("clients.ollama_client.httpx.AsyncClient", return_value=mock_cm):
            client = OllamaClient()
            result = await client.generate_lesson("test prompt")

        assert isinstance(result, LessonOutput)
        assert result.title == "Introduction to Python"
        assert result.estimated_minutes == 3
        assert result.key_takeaways == ["Easy to read", "Versatile"]

    async def test_generate_lesson_sends_correct_payload(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "llama3:8b")

        mock_cm = _mock_httpx_client({"response": json.dumps(VALID_LESSON)})
        with patch("clients.ollama_client.httpx.AsyncClient", return_value=mock_cm):
            client = OllamaClient()
            await client.generate_lesson("explain loops")

        mock_cm.__aenter__.return_value.post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": "explain loops",
                "format": "json",
                "stream": False,
            },
            timeout=60.0,
        )

    async def test_generate_quiz_returns_quiz_output(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "llama3:8b")

        mock_cm = _mock_httpx_client({"response": json.dumps(VALID_QUIZ)})
        with patch("clients.ollama_client.httpx.AsyncClient", return_value=mock_cm):
            client = OllamaClient()
            result = await client.generate_quiz("test prompt")

        assert isinstance(result, QuizOutput)
        assert result.question == "What type of language is Python?"
        assert len(result.options) == 4

    async def test_coaching_reply_returns_coaching_output(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "llama3:8b")

        mock_cm = _mock_httpx_client(
            {"message": {"content": json.dumps(VALID_COACHING)}}
        )
        with patch("clients.ollama_client.httpx.AsyncClient", return_value=mock_cm):
            client = OllamaClient()
            result = await client.coaching_reply(
                [{"role": "user", "content": "Help me understand loops"}]
            )

        assert isinstance(result, CoachingOutput)
        assert result.message == "Great question! Python's indentation enforces code structure."
        assert result.suggestions == ["Try the REPL", "Read PEP 8"]

    async def test_generate_lesson_raises_model_output_error_on_schema_mismatch(
        self, monkeypatch
    ):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "llama3:8b")

        # Missing required fields — will fail Pydantic validation
        mock_cm = _mock_httpx_client({"response": '{"title": "incomplete"}'})
        with patch("clients.ollama_client.httpx.AsyncClient", return_value=mock_cm):
            client = OllamaClient()
            with pytest.raises(ModelOutputError, match="Lesson output validation failed"):
                await client.generate_lesson("test prompt")

    async def test_generate_quiz_raises_model_output_error_on_invalid_json(
        self, monkeypatch
    ):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "llama3:8b")

        mock_cm = _mock_httpx_client({"response": "not valid json at all {{ }}"})
        with patch("clients.ollama_client.httpx.AsyncClient", return_value=mock_cm):
            client = OllamaClient()
            with pytest.raises(ModelOutputError, match="Quiz output validation failed"):
                await client.generate_quiz("test prompt")

    async def test_coaching_reply_raises_model_output_error_on_schema_mismatch(
        self, monkeypatch
    ):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "llama3:8b")

        # Missing required 'message' field
        mock_cm = _mock_httpx_client(
            {"message": {"content": '{"suggestions": ["only suggestions, no message"]}'}}
        )
        with patch("clients.ollama_client.httpx.AsyncClient", return_value=mock_cm):
            client = OllamaClient()
            with pytest.raises(ModelOutputError, match="Coaching output validation failed"):
                await client.coaching_reply([{"role": "user", "content": "help"}])


# ---------------------------------------------------------------------------
# VertexClient
# ---------------------------------------------------------------------------

class TestVertexClient:
    async def test_generate_lesson_returns_lesson_output(self, monkeypatch):
        monkeypatch.setenv("VERTEX_PROJECT", "test-project")
        monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
        monkeypatch.setenv("VERTEX_MODEL", "gemini-1.5-flash")

        mock_model = _mock_vertex_model(json.dumps(VALID_LESSON))
        with patch("clients.vertex_client.vertexai.init"), patch(
            "clients.vertex_client.GenerativeModel", return_value=mock_model
        ):
            client = VertexClient()
            result = await client.generate_lesson("test prompt")

        assert isinstance(result, LessonOutput)
        assert result.title == "Introduction to Python"

    async def test_generate_quiz_returns_quiz_output(self, monkeypatch):
        monkeypatch.setenv("VERTEX_PROJECT", "test-project")

        mock_model = _mock_vertex_model(json.dumps(VALID_QUIZ))
        with patch("clients.vertex_client.vertexai.init"), patch(
            "clients.vertex_client.GenerativeModel", return_value=mock_model
        ):
            client = VertexClient()
            result = await client.generate_quiz("test prompt")

        assert isinstance(result, QuizOutput)
        assert len(result.options) == 4

    async def test_coaching_reply_returns_coaching_output(self, monkeypatch):
        monkeypatch.setenv("VERTEX_PROJECT", "test-project")

        mock_model = _mock_vertex_model(json.dumps(VALID_COACHING))
        with patch("clients.vertex_client.vertexai.init"), patch(
            "clients.vertex_client.GenerativeModel", return_value=mock_model
        ):
            client = VertexClient()
            result = await client.coaching_reply(
                [
                    {"role": "assistant", "content": "How can I help?"},
                    {"role": "user", "content": "Explain decorators"},
                ]
            )

        assert isinstance(result, CoachingOutput)
        assert result.suggestions == ["Try the REPL", "Read PEP 8"]

    async def test_generate_lesson_raises_model_output_error_on_schema_mismatch(
        self, monkeypatch
    ):
        monkeypatch.setenv("VERTEX_PROJECT", "test-project")

        mock_model = _mock_vertex_model('{"title": "incomplete"}')
        with patch("clients.vertex_client.vertexai.init"), patch(
            "clients.vertex_client.GenerativeModel", return_value=mock_model
        ):
            client = VertexClient()
            with pytest.raises(ModelOutputError, match="Lesson output validation failed"):
                await client.generate_lesson("test prompt")


# ---------------------------------------------------------------------------
# get_model_client factory
# ---------------------------------------------------------------------------

class TestGetModelClient:
    def test_returns_ollama_client_by_default(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "ollama")
        client = get_model_client()
        assert isinstance(client, OllamaClient)

    def test_returns_ollama_client_when_provider_not_set(self, monkeypatch):
        monkeypatch.delenv("AI_PROVIDER", raising=False)
        client = get_model_client()
        assert isinstance(client, OllamaClient)

    def test_returns_vertex_client_for_vertex_provider(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "vertex")
        monkeypatch.setenv("VERTEX_PROJECT", "test-project")
        with patch("clients.vertex_client.vertexai.init"), patch(
            "clients.vertex_client.GenerativeModel"
        ):
            client = get_model_client()
        assert isinstance(client, VertexClient)
