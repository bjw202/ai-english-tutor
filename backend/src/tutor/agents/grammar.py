"""
Grammar analysis agent.

Uses GPT-4o to analyze text for grammatical patterns including:
- Tenses used in the text
- Voice (active/passive)
- Sentence structure type
- Detailed grammar analysis
"""

from __future__ import annotations

import logging

from tutor.models.llm import get_llm
from tutor.prompts import get_level_instructions, render_prompt
from tutor.schemas import GrammarResult
from tutor.state import TutorState

logger = logging.getLogger(__name__)


async def grammar_node(state: TutorState) -> dict:
    """
    Process text for grammar analysis.

    Uses GPT-4o to analyze the input text and extract grammatical
    patterns including tenses, voice, sentence structure, and analysis.

    Args:
        state: TutorState containing input_text and level

    Returns:
        Dictionary with "grammar_result" key containing GrammarResult or None on error
    """
    try:
        # Get the LLM client for grammar analysis
        llm = get_llm("gpt-4o")

        # Get state values with safe defaults
        level = state.get("level", 3)
        input_text = state.get("input_text", "")

        # Get level-specific instructions
        level_instructions = get_level_instructions(level)

        # Render prompt with level instructions
        prompt = render_prompt(
            "grammar.md",
            text=input_text,
            level=level,
            level_instructions=level_instructions,
        )

        # Use structured output for reliable JSON parsing
        structured_llm = llm.with_structured_output(GrammarResult)
        grammar_result = await structured_llm.ainvoke(prompt)

        return {"grammar_result": grammar_result}

    except Exception as e:
        logger.error(f"Error in grammar_node: {e}")
        return {"grammar_result": None}
