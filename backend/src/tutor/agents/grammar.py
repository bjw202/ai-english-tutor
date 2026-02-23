"""
Grammar analysis agent - Korean structure-focused grammar explanation.

Uses GPT-4o to generate Korean Markdown grammar explanation content
focusing on structural understanding rather than terminology listing.
"""

from __future__ import annotations

import logging

from tutor.config import get_settings
from tutor.models.llm import get_llm
from tutor.prompts import get_level_instructions, render_prompt
from tutor.schemas import GrammarResult
from tutor.state import TutorState
from tutor.utils.markdown_normalizer import normalize_grammar_output

logger = logging.getLogger(__name__)


async def grammar_node(state: TutorState) -> dict:
    """
    Process text for grammar analysis with Korean structural explanation.

    Uses GPT-4o to generate Korean Markdown grammar explanation content
    including sentence-by-sentence structural breakdown.

    Args:
        state: TutorState containing input_text, level, and supervisor_analysis

    Returns:
        Dictionary with "grammar_result" key containing GrammarResult or None on error
    """
    try:
        settings = get_settings()
        llm = get_llm(settings.GRAMMAR_MODEL)

        level = state.get("level", 3)
        input_text = state.get("input_text", "")
        level_instructions = get_level_instructions(level)

        # Get supervisor analysis if available
        supervisor_analysis = state.get("supervisor_analysis")
        supervisor_context = ""
        if supervisor_analysis:
            supervisor_context = (
                f"\n\n[사전 분석]\n"
                f"전체 난이도: {supervisor_analysis.overall_difficulty}/5\n"
                f"학습 포커스: {', '.join(supervisor_analysis.focus_summary)}"
            )

        prompt = render_prompt(
            "grammar.md",
            text=input_text,
            level=level,
            level_instructions=level_instructions,
            supervisor_context=supervisor_context,
        )

        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = normalize_grammar_output(content)
        return {"grammar_result": GrammarResult(content=content)}

    except Exception as e:
        logger.error(f"Error in grammar_node: {e}")
        return {"grammar_result": None}
