from abc import ABC, abstractmethod

from models.schemas import CoachingOutput, LessonOutput, QuizOutput


class ModelOutputError(Exception):
    """Raised when model output cannot be validated against the expected schema."""
    pass


class BaseModelClient(ABC):
    @abstractmethod
    async def generate_lesson(self, prompt: str) -> LessonOutput: ...

    @abstractmethod
    async def generate_quiz(self, prompt: str) -> QuizOutput: ...

    @abstractmethod
    async def coaching_reply(self, messages: list[dict]) -> CoachingOutput: ...
