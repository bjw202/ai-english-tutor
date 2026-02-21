"""
Vocabulary extraction agent.

Uses Claude Haiku to extract vocabulary words from text including:
- Word terms
- Definitions
- Usage examples
- Synonyms
"""

from __future__ import annotations

import logging

from tutor.models.llm import get_llm
from tutor.prompts import get_level_instructions, render_prompt
from tutor.schemas import VocabularyResult
from tutor.state import TutorState

logger = logging.getLogger(__name__)


async def vocabulary_node(state: TutorState) -> dict:
    """
    Process text for vocabulary extraction.

    Uses Claude Haiku (claude-haiku-4-5) to analyze the input text
    and extract vocabulary words with definitions, usage examples, and synonyms.

    Args:
        state: TutorState containing input_text and level

    Returns:
        Dictionary with "vocabulary_result" key containing VocabularyResult or None on error
    """
    try:
        # Get the LLM client for vocabulary extraction
        llm = get_llm("claude-haiku-4-5")

        # Get state values with safe defaults
        level = state.get("level", 3)
        input_text = state.get("input_text", "")

        # Get level-specific instructions
        level_instructions = get_level_instructions(level)

        # Render prompt with level instructions
        prompt = render_prompt(
            "vocabulary.md",
            text=input_text,
            level=level,
            level_instructions=level_instructions,
        )

        # Use structured output for reliable JSON parsing
        structured_llm = llm.with_structured_output(VocabularyResult)
        vocabulary_result = await structured_llm.ainvoke(prompt)

        return {"vocabulary_result": vocabulary_result}

    except Exception as e:
        logger.error(f"Error in vocabulary_node: {e}")
        return {"vocabulary_result": None}
