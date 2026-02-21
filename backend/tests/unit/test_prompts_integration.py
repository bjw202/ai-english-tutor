"""
Integration tests for prompt loading system.

These tests verify that the actual prompt files are correctly structured.
"""

from tutor.prompts import get_level_instructions, load_prompt, render_prompt


class TestPromptFiles:
    """Test cases for actual prompt file integrity."""

    def test_supervisor_prompt_exists(self):
        """Test that supervisor.md can be loaded."""
        result = load_prompt("supervisor.md")
        assert "supervisor" in result.lower()
        assert "{task_type}" in result
        assert "{user_input}" in result

    def test_reading_prompt_exists(self):
        """Test that reading.md can be loaded."""
        result = load_prompt("reading.md")
        assert "reading" in result.lower()
        assert "{text}" in result
        assert "{level}" in result
        assert "{level_instructions}" in result

    def test_grammar_prompt_exists(self):
        """Test that grammar.md can be loaded."""
        result = load_prompt("grammar.md")
        assert "grammar" in result.lower()
        assert "{text}" in result
        assert "{level}" in result

    def test_vocabulary_prompt_exists(self):
        """Test that vocabulary.md can be loaded."""
        result = load_prompt("vocabulary.md")
        assert "vocabulary" in result.lower()
        assert "{text}" in result
        assert "{level}" in result

    def test_render_supervisor_prompt(self):
        """Test rendering supervisor prompt with variables."""
        result = render_prompt(
            "supervisor.md", task_type="reading", user_input="Analyze this text."
        )
        assert "reading" in result
        assert "Analyze this text." in result

    def test_render_reading_prompt(self):
        """Test rendering reading prompt with variables."""
        level_inst = get_level_instructions(3)
        result = render_prompt(
            "reading.md", text="This is a test.", level=3, level_instructions=level_inst
        )
        assert "This is a test." in result
        assert "3" in result


class TestLevelInstructions:
    """Test cases for actual level_instructions.yaml content."""

    def test_all_levels_1_to_5_exist(self):
        """Test that all levels 1-5 can be loaded."""
        for level in range(1, 6):
            result = get_level_instructions(level)
            assert result  # Should not be empty
            assert len(result) > 50  # Should have substantial content

    def test_level_1_simple_instructions(self):
        """Test that level 1 has simple, age-appropriate instructions."""
        result = get_level_instructions(1)
        assert "simple" in result.lower()
        assert "korean" in result.lower()

    def test_level_5_advanced_instructions(self):
        """Test that level 5 has advanced, academic instructions."""
        result = get_level_instructions(5)
        assert "academic" in result.lower() or "advanced" in result.lower()
