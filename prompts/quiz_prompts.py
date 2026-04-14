from models.schemas import QuizRequest

_SCHEMA = """{
  "question": "<multiple choice question about the lesson>",
  "options": ["<option A>", "<option B>", "<option C>", "<option D>"],
  "correct_answer": "<the correct option, must match one of the options exactly>",
  "explanation": "<why the correct answer is right>"
}"""


def build_quiz_prompt(request: QuizRequest) -> str:
    return f"""You are an expert educational content creator. Generate one multiple-choice quiz question based on the lesson below.

Skill level: {request.skill_level}

Lesson content:
{request.lesson_content}

Requirements:
- Write exactly 4 answer options
- The correct_answer field must exactly match one of the options
- The explanation should reinforce the correct concept in 1-2 sentences
- Match the difficulty to the skill level: {request.skill_level}

Return ONLY a JSON object with this exact structure — no markdown, no explanation, no text before or after:
{_SCHEMA}"""
