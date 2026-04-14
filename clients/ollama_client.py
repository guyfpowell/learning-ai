import os

import httpx
from pydantic import ValidationError

from clients.base import BaseModelClient, ModelOutputError
from models.schemas import CoachingOutput, LessonOutput, QuizOutput


class OllamaClient(BaseModelClient):
    def __init__(self) -> None:
        self._base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3:8b")

    async def _generate(self, prompt: str) -> str:
        """POST to /api/generate and return the raw response string."""
        payload = {
            "model": self._model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()["response"]

    async def _chat(self, messages: list[dict]) -> str:
        """POST to /api/chat and return the raw response string."""
        payload = {
            "model": self._model,
            "messages": messages,
            "format": "json",
            "stream": False,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]

    async def generate_lesson(self, prompt: str) -> LessonOutput:
        raw = await self._generate(prompt)
        try:
            return LessonOutput.model_validate_json(raw)
        except (ValidationError, ValueError) as e:
            raise ModelOutputError(f"Lesson output validation failed: {e}") from e

    async def generate_quiz(self, prompt: str) -> QuizOutput:
        raw = await self._generate(prompt)
        try:
            return QuizOutput.model_validate_json(raw)
        except (ValidationError, ValueError) as e:
            raise ModelOutputError(f"Quiz output validation failed: {e}") from e

    async def coaching_reply(self, messages: list[dict]) -> CoachingOutput:
        raw = await self._chat(messages)
        try:
            return CoachingOutput.model_validate_json(raw)
        except (ValidationError, ValueError) as e:
            raise ModelOutputError(f"Coaching output validation failed: {e}") from e
