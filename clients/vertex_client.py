import os

import vertexai
from pydantic import ValidationError
from vertexai.generative_models import GenerationConfig, GenerativeModel

from clients.base import BaseModelClient, ModelOutputError
from models.schemas import CoachingOutput, LessonOutput, QuizOutput


class VertexClient(BaseModelClient):
    def __init__(self) -> None:
        project = os.getenv("VERTEX_PROJECT")
        location = os.getenv("VERTEX_LOCATION", "us-central1")
        model_name = os.getenv("VERTEX_MODEL", "gemini-1.5-flash")
        vertexai.init(project=project, location=location)
        self._model = GenerativeModel(model_name)
        self._generation_config = GenerationConfig(response_mime_type="application/json")

    async def _generate_json(self, prompt: str) -> str:
        response = await self._model.generate_content_async(
            prompt,
            generation_config=self._generation_config,
        )
        return response.text

    async def generate_lesson(self, prompt: str) -> LessonOutput:
        raw = await self._generate_json(prompt)
        try:
            return LessonOutput.model_validate_json(raw)
        except (ValidationError, ValueError) as e:
            raise ModelOutputError(f"Lesson output validation failed: {e}") from e

    async def generate_quiz(self, prompt: str) -> QuizOutput:
        raw = await self._generate_json(prompt)
        try:
            return QuizOutput.model_validate_json(raw)
        except (ValidationError, ValueError) as e:
            raise ModelOutputError(f"Quiz output validation failed: {e}") from e

    async def coaching_reply(self, messages: list[dict]) -> CoachingOutput:
        conversation = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in messages
        )
        raw = await self._generate_json(conversation)
        try:
            return CoachingOutput.model_validate_json(raw)
        except (ValidationError, ValueError) as e:
            raise ModelOutputError(f"Coaching output validation failed: {e}") from e
