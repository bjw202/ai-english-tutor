"""
Integration tests for prompt loading system (SPEC-UPDATE-001).

These tests verify that the actual prompt files are correctly structured
for the Korean tutoring prompt redesign.
"""

from tutor.prompts import get_level_instructions, load_prompt, render_prompt


class TestPromptFiles:
    """Test cases for actual prompt file integrity (SPEC-UPDATE-001 Korean prompts)."""

    def test_supervisor_prompt_exists(self):
        """Test that supervisor.md can be loaded as documentation file."""
        result = load_prompt("supervisor.md")
        # supervisor.md is now a documentation-only file (supervisor builds prompts inline)
        assert len(result) > 0
        assert "supervisor" in result.lower()

    def test_reading_prompt_exists(self):
        """Test that reading.md can be loaded and has required template variables."""
        result = load_prompt("reading.md")
        assert "{text}" in result
        assert "{level}" in result
        assert "{level_instructions}" in result
        assert "{supervisor_context}" in result

    def test_grammar_prompt_exists(self):
        """Test that grammar.md can be loaded and has required template variables."""
        result = load_prompt("grammar.md")
        assert "{text}" in result
        assert "{level}" in result
        assert "{level_instructions}" in result
        assert "{supervisor_context}" in result

    def test_vocabulary_prompt_exists(self):
        """Test that vocabulary.md can be loaded and has required template variables."""
        result = load_prompt("vocabulary.md")
        assert "{text}" in result
        assert "{level}" in result
        assert "{level_instructions}" in result
        assert "{supervisor_context}" in result

    def test_reading_prompt_korean_content(self):
        """Test that reading.md is written in Korean (SPEC-UPDATE-001)."""
        result = load_prompt("reading.md")
        # Korean prompts contain Korean characters and terminology
        assert "슬래시" in result or "직독" in result or "한국어" in result

    def test_grammar_prompt_korean_content(self):
        """Test that grammar.md is written in Korean (SPEC-UPDATE-001)."""
        result = load_prompt("grammar.md")
        # Korean prompts contain Korean grammar terminology
        assert "문법" in result or "구조" in result

    def test_vocabulary_prompt_korean_content(self):
        """Test that vocabulary.md is written in Korean (SPEC-UPDATE-001)."""
        result = load_prompt("vocabulary.md")
        # Korean vocabulary prompts contain Korean etymology-related terminology
        assert "어원" in result or "단어" in result

    def test_vocabulary_prompt_has_markdown_header_format(self):
        """Test that vocabulary.md instructs LLM to use ## word headers."""
        result = load_prompt("vocabulary.md")
        # Vocabulary parser expects ## [word] format from the LLM
        assert "## " in result

    def test_render_reading_prompt(self):
        """Test rendering reading prompt with all required variables (SPEC-UPDATE-001)."""
        level_inst = get_level_instructions(3)
        result = render_prompt(
            "reading.md",
            text="This is a test.",
            level=3,
            level_instructions=level_inst,
            supervisor_context="",
        )
        assert "This is a test." in result
        assert "3" in result

    def test_render_grammar_prompt(self):
        """Test rendering grammar prompt with all required variables."""
        level_inst = get_level_instructions(2)
        result = render_prompt(
            "grammar.md",
            text="The cat sat on the mat.",
            level=2,
            level_instructions=level_inst,
            supervisor_context="",
        )
        assert "The cat sat on the mat." in result
        assert "2" in result

    def test_render_vocabulary_prompt(self):
        """Test rendering vocabulary prompt with all required variables."""
        level_inst = get_level_instructions(4)
        result = render_prompt(
            "vocabulary.md",
            text="The ephemeral beauty of cherry blossoms.",
            level=4,
            level_instructions=level_inst,
            supervisor_context="",
        )
        assert "ephemeral" in result
        assert "4" in result

    def test_render_reading_prompt_with_supervisor_context(self):
        """Test rendering reading prompt includes supervisor context when provided."""
        level_inst = get_level_instructions(3)
        supervisor_ctx = "\n\n[사전 분석]\n전체 난이도: 3/5\n학습 포커스: reading, grammar"
        result = render_prompt(
            "reading.md",
            text="Hello world.",
            level=3,
            level_instructions=level_inst,
            supervisor_context=supervisor_ctx,
        )
        assert "사전 분석" in result
        assert "Hello world." in result


class TestLevelInstructions:
    """Test cases for actual level_instructions.yaml content (SPEC-UPDATE-001 Korean)."""

    def test_all_levels_1_to_5_exist(self):
        """Test that all levels 1-5 can be loaded."""
        for level in range(1, 6):
            result = get_level_instructions(level)
            assert result  # Should not be empty
            assert len(result) > 50  # Should have substantial content

    def test_level_1_simple_instructions(self):
        """Test that level 1 has beginner-level Korean instructions (SPEC-UPDATE-001)."""
        result = get_level_instructions(1)
        # Level 1 is "초급 - 초등 고학년" in Korean
        assert "쉬운" in result or "간단" in result or "초급" in result or "초등" in result

    def test_level_5_advanced_instructions(self):
        """Test that level 5 has advanced Korean instructions (SPEC-UPDATE-001)."""
        result = get_level_instructions(5)
        # Level 5 is "고급 - 수능/내신 최상위" in Korean
        assert "고급" in result or "전문" in result or "수능" in result or "대학" in result

    def test_level_instructions_are_korean(self):
        """Test that level instructions contain Korean characters (SPEC-UPDATE-001)."""
        for level in range(1, 6):
            result = get_level_instructions(level)
            # Check for Korean Unicode range (Hangul syllables block: AC00-D7A3)
            has_korean = any("\uAC00" <= ch <= "\uD7A3" for ch in result)
            assert has_korean, f"Level {level} instructions should contain Korean text"

    def test_level_3_intermediate_instructions(self):
        """Test that level 3 has intermediate Korean instructions."""
        result = get_level_instructions(3)
        # Level 3 is "기초 - 중학교 2-3학년" - includes grammar terminology
        assert "문법" in result or "중학교" in result or "교육" in result

    def test_level_4_high_school_instructions(self):
        """Test that level 4 has high school level Korean instructions."""
        result = get_level_instructions(4)
        # Level 4 is "중급 - 고등학교 수준"
        assert "고등" in result or "수능" in result or "시험" in result
