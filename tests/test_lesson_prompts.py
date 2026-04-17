"""Unit tests for build_lesson_prompt() learning style variant selection."""
import pytest
from models.schemas import LessonRequest
from prompts.lesson_prompts import build_lesson_prompt


def _make_request(learning_style: str = "general", skill_level: str = "beginner") -> LessonRequest:
    return LessonRequest(
        skill_id="python-basics",
        skill_level=skill_level,
        topic="Python variables",
        user_context={
            "goal": "learn Python",
            "learning_style": learning_style,
            "completed_lessons": 2,
        },
        tier="free",
    )


class TestVisualConciseStyle:
    def test_prompt_contains_bullet_point_instruction(self):
        prompt = build_lesson_prompt(_make_request("visual-concise"))
        assert "bullet" in prompt.lower()

    def test_schema_shows_two_minute_estimate(self):
        prompt = build_lesson_prompt(_make_request("visual-concise"))
        assert '"estimated_minutes": 2' in prompt

    def test_prompt_contains_250_words_hint(self):
        prompt = build_lesson_prompt(_make_request("visual-concise"))
        assert "250" in prompt


class TestDetailedNarrativeStyle:
    def test_prompt_contains_narrative_instruction(self):
        prompt = build_lesson_prompt(_make_request("detailed-narrative"))
        assert "narrative" in prompt.lower() or "examples" in prompt.lower()

    def test_schema_shows_five_minute_estimate(self):
        prompt = build_lesson_prompt(_make_request("detailed-narrative"))
        assert '"estimated_minutes": 5' in prompt

    def test_prompt_contains_500_words_hint(self):
        prompt = build_lesson_prompt(_make_request("detailed-narrative"))
        assert "500" in prompt


class TestReinforcementStyle:
    def test_prompt_contains_recap_instruction(self):
        prompt = build_lesson_prompt(_make_request("reinforcement"))
        assert "recap" in prompt.lower() or "prior" in prompt.lower()

    def test_schema_shows_three_minute_estimate(self):
        prompt = build_lesson_prompt(_make_request("reinforcement"))
        assert '"estimated_minutes": 3' in prompt


class TestGeneralStyle:
    def test_schema_shows_three_minute_estimate(self):
        prompt = build_lesson_prompt(_make_request("general"))
        assert '"estimated_minutes": 3' in prompt

    def test_prompt_contains_400_words_hint(self):
        prompt = build_lesson_prompt(_make_request("general"))
        assert "400" in prompt


class TestStyleFallback:
    def test_unknown_style_falls_back_to_general(self):
        prompt = build_lesson_prompt(_make_request("unknown-style"))
        # Should not raise and should produce a general-style prompt
        assert '"estimated_minutes": 3' in prompt
        assert "400" in prompt

    def test_missing_learning_style_falls_back_to_general(self):
        request = LessonRequest(
            skill_id="s1",
            skill_level="beginner",
            topic="topic",
            user_context={},  # no learning_style key
            tier="free",
        )
        prompt = build_lesson_prompt(request)
        assert '"estimated_minutes": 3' in prompt


class TestPromptAlwaysContainsTopicAndLevel:
    """Style variants must not drop topic or skill level from the prompt."""

    @pytest.mark.parametrize("style", ["visual-concise", "detailed-narrative", "reinforcement", "general"])
    def test_topic_always_in_prompt(self, style: str):
        prompt = build_lesson_prompt(_make_request(style))
        assert "Python variables" in prompt

    @pytest.mark.parametrize("style", ["visual-concise", "detailed-narrative", "reinforcement", "general"])
    def test_skill_level_always_in_prompt(self, style: str):
        prompt = build_lesson_prompt(_make_request(style))
        assert "beginner" in prompt
