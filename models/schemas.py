from pydantic import BaseModel


class LessonRequest(BaseModel):
    skill_id: str
    skill_level: str  # beginner | intermediate | advanced
    topic: str
    user_context: dict  # goal, learning_style, completed_lessons count
    tier: str           # free | starter | pro | premium


class QuizRequest(BaseModel):
    lesson_content: str
    skill_level: str
    tier: str


class CoachingRequest(BaseModel):
    messages: list[dict]  # [{role: user|assistant, content: str}]
    lesson_context: str
    user_context: dict
    tier: str


class QuizOutput(BaseModel):
    question: str
    options: list[str]      # exactly 4 items
    correct_answer: str     # must be one of options
    explanation: str


class LessonOutput(BaseModel):
    title: str
    content: str
    estimated_minutes: int
    key_takeaways: list[str]
    quiz: QuizOutput


class CoachingOutput(BaseModel):
    message: str
    suggestions: list[str] = []
