"""
Unit tests for prompt loading system.

Tests follow the RED-GREEN-REFACTOR TDD cycle.
"""

import pytest
import yaml

from tutor.prompts import get_level_instructions, load_prompt, render_prompt


class TestLoadPrompt:
    """Test cases for load_prompt function."""

    def test_load_prompt_existing_file(self, tmp_path):
        """Test loading an existing prompt file."""
        # Arrange: Create a test prompt file
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        test_file = prompts_dir / "test_prompt.md"
        test_file.write_text("Hello {name}, this is a test prompt.")

        # Act: Load the prompt
        result = load_prompt(str(test_file))

        # Assert: Verify content is loaded
        assert result == "Hello {name}, this is a test prompt."

    def test_load_prompt_nonexistent_file(self):
        """Test loading a non-existent prompt file raises FileNotFoundError."""
        # Act & Assert: Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            load_prompt("nonexistent_prompt.md")


class TestRenderPrompt:
    """Test cases for render_prompt function."""

    def test_render_prompt_with_variables(self, tmp_path, monkeypatch):
        """Test rendering a prompt with variable substitution."""
        # Arrange: Create a test prompt file
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        test_file = prompts_dir / "test_prompt.md"
        test_file.write_text("Hello {name}, level: {level}.")

        # Mock the prompts directory path
        monkeypatch.setattr("tutor.prompts.PROMPTS_DIR", prompts_dir)

        # Act: Render the prompt with variables
        result = render_prompt("test_prompt.md", name="Alice", level=3)

        # Assert: Verify variables are substituted
        assert result == "Hello Alice, level: 3."

    def test_render_prompt_missing_variable(self, tmp_path, monkeypatch):
        """Test rendering with missing variable raises KeyError."""
        # Arrange: Create a test prompt file with a variable
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        test_file = prompts_dir / "test_prompt.md"
        test_file.write_text("Hello {name}.")

        # Mock the prompts directory path
        monkeypatch.setattr("tutor.prompts.PROMPTS_DIR", prompts_dir)

        # Act & Assert: Should raise KeyError for missing variable
        with pytest.raises(KeyError):
            render_prompt("test_prompt.md")  # 'name' not provided


class TestGetLevelInstructions:
    """Test cases for get_level_instructions function."""

    @pytest.fixture(autouse=True)
    def reset_cache(self, monkeypatch):
        """Reset the level instructions cache before each test."""
        monkeypatch.setattr("tutor.prompts._level_instructions_cache", None)

    def test_get_level_instructions_valid_level(self, tmp_path, monkeypatch):
        """Test getting instructions for a valid level."""
        # Arrange: Create a level_instructions.yaml file
        level_file = tmp_path / "level_instructions.yaml"
        level_data = {
            "levels": {
                1: {"description": "Beginner", "instructions": "Use simple words."},
                3: {"description": "Intermediate", "instructions": "Use normal examples."},
            }
        }
        level_file.write_text(yaml.dump(level_data))

        # Mock the prompts directory path
        monkeypatch.setattr("tutor.prompts.LEVEL_INSTRUCTIONS_PATH", level_file)

        # Act: Get instructions for level 3
        result = get_level_instructions(3)

        # Assert: Verify correct instructions returned
        assert result == "Use normal examples."

    def test_get_level_instructions_invalid_level(self, tmp_path, monkeypatch):
        """Test getting instructions for an invalid level."""
        # Arrange: Create a level_instructions.yaml file
        level_file = tmp_path / "level_instructions.yaml"
        level_data = {
            "levels": {1: {"description": "Beginner", "instructions": "Use simple words."}}
        }
        level_file.write_text(yaml.dump(level_data))

        # Mock the prompts directory path
        monkeypatch.setattr("tutor.prompts.LEVEL_INSTRUCTIONS_PATH", level_file)

        # Act & Assert: Should raise ValueError for invalid level
        with pytest.raises(ValueError, match="Invalid comprehension level"):
            get_level_instructions(99)

    def test_get_level_instructions_all_levels(self, tmp_path, monkeypatch):
        """Test that all levels 1-5 are available."""
        # Arrange: Create a complete level_instructions.yaml file
        level_file = tmp_path / "level_instructions.yaml"
        level_data = {
            "levels": {
                1: {"description": "Very Basic", "instructions": "Level 1 instructions"},
                2: {"description": "Basic", "instructions": "Level 2 instructions"},
                3: {"description": "Intermediate", "instructions": "Level 3 instructions"},
                4: {"description": "Advanced", "instructions": "Level 4 instructions"},
                5: {"description": "Expert", "instructions": "Level 5 instructions"},
            }
        }
        level_file.write_text(yaml.dump(level_data))

        # Mock the prompts directory path
        monkeypatch.setattr("tutor.prompts.LEVEL_INSTRUCTIONS_PATH", level_file)

        # Act & Assert: Verify all levels work
        for level in range(1, 6):
            result = get_level_instructions(level)
            assert result == f"Level {level} instructions"
