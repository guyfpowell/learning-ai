from models.schemas import LessonRequest

_SKILL_LEVEL_INSTRUCTIONS = {
    "beginner": "Use simple language, avoid jargon, and explain concepts from scratch. Assume no prior knowledge.",
    "intermediate": "Assume basic familiarity with the topic. Use correct terminology and build on foundational concepts.",
    "advanced": "Assume strong existing knowledge. Focus on nuance, edge cases, and deeper understanding.",
}

_SCHEMA = """{
  "title": "<concise lesson title>",
  "content": "<lesson content as plain text, 3 minutes to read, ~400 words>",
  "estimated_minutes": 3,
  "key_takeaways": ["<takeaway 1>", "<takeaway 2>", "<takeaway 3>"],
  "quiz": {
    "question": "<multiple choice question about the lesson>",
    "options": ["<option A>", "<option B>", "<option C>", "<option D>"],
    "correct_answer": "<the correct option, must match one of the options exactly>",
    "explanation": "<why the correct answer is right>"
  }
}"""


def build_lesson_prompt(request: LessonRequest) -> str:
    level_instruction = _SKILL_LEVEL_INSTRUCTIONS.get(
        request.skill_level, _SKILL_LEVEL_INSTRUCTIONS["beginner"]
    )
    goal = request.user_context.get("goal", "learn the topic")
    learning_style = request.user_context.get("learning_style", "general")
    completed = request.user_context.get("completed_lessons", 0)

    return f"""You are an expert educational content creator. Generate a focused micro-lesson.

Topic: {request.topic}
Skill level: {request.skill_level}
Learner goal: {goal}
Learning style: {learning_style}
Lessons completed so far: {completed}

Level guidance: {level_instruction}

Requirements:
- The lesson should take approximately 3 minutes to read (~400 words of content)
- Write 3 key takeaways as short, memorable bullet points
- Include one multiple-choice quiz question with exactly 4 options
- The correct_answer field must exactly match one of the options

Return ONLY a JSON object with this exact structure — no markdown, no explanation, no text before or after:
{_SCHEMA}"""
