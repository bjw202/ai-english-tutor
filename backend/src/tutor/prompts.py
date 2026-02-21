"""
Prompt loading system for AI English Tutor.

Loads prompt templates from .md files and provides variable substitution.
Also manages level-specific instructions for different comprehension levels.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    pass

# Directory paths
PROMPTS_DIR = Path(__file__).parent / "prompts"
LEVEL_INSTRUCTIONS_PATH = PROMPTS_DIR / "level_instructions.yaml"

# Cache for level instructions (YAML uses int keys for levels 1-5)
_level_instructions_cache: dict[int, dict[str, str]] | None = None


def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        prompt_name: Name of the prompt file (can include path)

    Returns:
        Raw prompt template content as string

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    prompt_path = PROMPTS_DIR / prompt_name

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")


def render_prompt(prompt_name: str, **variables) -> str:
    """
    Load and render a prompt with variable substitution.

    Args:
        prompt_name: Name of the prompt file
        **variables: Keyword arguments for template variables

    Returns:
        Rendered prompt with variables substituted

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        KeyError: If a required variable is not provided
    """
    template = load_prompt(prompt_name)
    return template.format(**variables)


def _load_level_instructions() -> dict[str, dict[int, dict[str, str]]]:
    """
    Load level instructions from YAML file.

    Returns:
        Dictionary with level data

    Raises:
        FileNotFoundError: If level_instructions.yaml doesn't exist
    """
    if not LEVEL_INSTRUCTIONS_PATH.exists():
        raise FileNotFoundError(f"Level instructions file not found: {LEVEL_INSTRUCTIONS_PATH}")

    with open(LEVEL_INSTRUCTIONS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data


def get_level_instructions(level: int) -> str:
    """
    Get instructions for a specific comprehension level.

    Args:
        level: Comprehension level (1-5)

    Returns:
        Instruction string for the specified level

    Raises:
        ValueError: If level is not in valid range (1-5)
        FileNotFoundError: If level_instructions.yaml doesn't exist
    """
    global _level_instructions_cache

    # Load cache if not already loaded
    if _level_instructions_cache is None:
        data = _load_level_instructions()
        _level_instructions_cache = data.get("levels", {})

    # Get instructions for the specified level
    if _level_instructions_cache is None or level not in _level_instructions_cache:
        raise ValueError(f"Invalid comprehension level: {level}. Must be 1-5.")

    level_data = _level_instructions_cache[level]
    return level_data.get("instructions", "")
