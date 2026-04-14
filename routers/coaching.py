from fastapi import APIRouter, HTTPException

from clients import get_model_client
from clients.base import ModelOutputError
from models.schemas import CoachingOutput, CoachingRequest

router = APIRouter()

_SYSTEM_TEMPLATE = (
    "You are a helpful AI learning coach. "
    "The learner's goal is: {goal}. "
    "Their skill level is: {skill_level}.\n\n"
    "Current lesson context:\n{lesson_context}\n\n"
    "Answer questions about this lesson, provide encouragement, and offer clear explanations. "
    "Keep responses concise (2-4 sentences). "
    "Return ONLY a JSON object with this exact structure — "
    "no markdown, no explanation, no text before or after:\n"
    '{{"message": "<your coaching response>", '
    '"suggestions": ["<optional follow-up question or tip>"]}}'
)


def _build_messages(request: CoachingRequest) -> list[dict]:
    """Prepend a system message with lesson and user context, then conversation history."""
    goal = request.user_context.get("goal", "learn the topic")
    skill_level = request.user_context.get("skill_level", "beginner")
    system_content = _SYSTEM_TEMPLATE.format(
        goal=goal,
        skill_level=skill_level,
        lesson_context=request.lesson_context,
    )
    return [{"role": "system", "content": system_content}] + request.messages


@router.post("/message", response_model=CoachingOutput)
async def coaching_message(request: CoachingRequest):
    client = get_model_client()
    messages = _build_messages(request)
    try:
        return await client.coaching_reply(messages)
    except ModelOutputError as e:
        raise HTTPException(status_code=502, detail=str(e))
