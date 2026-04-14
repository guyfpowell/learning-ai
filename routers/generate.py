from fastapi import APIRouter, HTTPException

from clients import get_model_client
from clients.base import ModelOutputError
from models.schemas import LessonOutput, LessonRequest, QuizOutput, QuizRequest
from prompts.lesson_prompts import build_lesson_prompt
from prompts.quiz_prompts import build_quiz_prompt

router = APIRouter()


@router.post("/lesson", response_model=LessonOutput)
async def generate_lesson(request: LessonRequest):
    client = get_model_client()
    prompt = build_lesson_prompt(request)
    try:
        return await client.generate_lesson(prompt)
    except ModelOutputError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/quiz", response_model=QuizOutput)
async def generate_quiz(request: QuizRequest):
    client = get_model_client()
    prompt = build_quiz_prompt(request)
    try:
        return await client.generate_quiz(prompt)
    except ModelOutputError as e:
        raise HTTPException(status_code=502, detail=str(e))
