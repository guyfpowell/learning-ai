from models.schemas import LessonRequest

_SKILL_LEVEL_INSTRUCTIONS = {
    "beginner": "Use simple language, avoid jargon, and explain concepts from scratch. Assume no prior knowledge.",
    "intermediate": "Assume basic familiarity with the topic. Use correct terminology and build on foundational concepts.",
    "advanced": "Assume strong existing knowledge. Focus on nuance, edge cases, and deeper understanding.",
}

_LEARNING_STYLE_INSTRUCTIONS = {
    "visual-concise": (
        "Use bullet points, short sentences, and headers where helpful. "
        "Keep content brief and scannable. Target ~250 words and 2 minutes to read."
    ),
    "detailed-narrative": (
        "Use flowing narrative prose with concrete examples and real-world context. "
        "Build concepts step by step. Target ~500 words and 5 minutes to read."
    ),
    "reinforcement": (
        "Open by briefly recapping what the learner already knows, then build on it. "
        "Use spaced-repetition framing — connect new concepts to prior lessons. "
        "Target ~400 words and 3 minutes to read."
    ),
    "general": "Clear, structured prose. Target ~400 words and 3 minutes to read.",
}

_STYLE_CONFIG = {
    "visual-concise":     {"content_hint": "~250 words, bullet-point format", "minutes": 2},
    "detailed-narrative": {"content_hint": "~500 words, narrative prose with examples", "minutes": 5},
    "reinforcement":      {"content_hint": "~400 words, connects to prior learning", "minutes": 3},
    "general":            {"content_hint": "~400 words, clear prose", "minutes": 3},
}

_SCHEMA_TEMPLATE = """{
  "title": "<concise lesson title>",
  "content": "<lesson content as plain text, {content_hint}>",
  "estimated_minutes": {minutes},
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

    if learning_style not in _LEARNING_STYLE_INSTRUCTIONS:
        learning_style = "general"

    style_instruction = _LEARNING_STYLE_INSTRUCTIONS[learning_style]
    config = _STYLE_CONFIG[learning_style]
    schema = (
        _SCHEMA_TEMPLATE
        .replace("{content_hint}", config["content_hint"])
        .replace("{minutes}", str(config["minutes"]))
    )

    return f"""You are an expert educational content creator. Generate a focused micro-lesson.

Topic: {request.topic}
Skill level: {request.skill_level}
Learner goal: {goal}
Lessons completed so far: {completed}

Level guidance: {level_instruction}
Style guidance: {style_instruction}

Requirements:
- Write 3 key takeaways as short, memorable bullet points
- Include one multiple-choice quiz question with exactly 4 options
- The correct_answer field must exactly match one of the options

Return ONLY a JSON object with this exact structure — no markdown, no explanation, no text before or after:
{schema}"""
