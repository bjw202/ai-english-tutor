"""
Reading comprehension agent.

Uses Claude Sonnet to analyze text for reading comprehension including:
- Summary of the text content
- Main topic identification
- Emotional tone detection
"""

from __future__ import annotations

import logging

from tutor.models.llm import get_llm
from tutor.prompts import get_level_instructions, render_prompt
from tutor.schemas import ReadingResult
from tutor.state import TutorState

logger = logging.getLogger(__name__)


async def reading_node(state: TutorState) -> dict:
    """
    Process text for reading comprehension analysis.

    Uses Claude Sonnet (claude-sonnet-4-5) to analyze the input text
    and extract summary, main topic, and emotional tone.

    Args:
        state: TutorState containing input_text and level

    Returns:
        Dictionary with "reading_result" key containing ReadingResult or None on error
    """
    try:
        # Get the LLM client for reading analysis
        llm = get_llm("claude-sonnet-4-5")

        # Get state values with safe defaults
        level = state.get("level", 3)
        input_text = state.get("input_text", "")

        # Get level-specific instructions
        level_instructions = get_level_instructions(level)

        # Render prompt with level instructions
        prompt = render_prompt(
            "reading.md",
            text=input_text,
            level=level,
            level_instructions=level_instructions,
        )

        # Use structured output for reliable JSON parsing
        structured_llm = llm.with_structured_output(ReadingResult)
        reading_result = await structured_llm.ainvoke(prompt)

        return {"reading_result": reading_result}

    except Exception as e:
        logger.error(f"Error in reading_node: {e}")
        return {"reading_result": None}
