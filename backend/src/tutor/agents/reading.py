"""
Reading training agent - Korean slash reading method.

Uses Claude Sonnet to generate Korean Markdown reading training content
including slash reading (직독직해) for each sentence.
"""

from __future__ import annotations

import logging

from tutor.config import get_settings
from tutor.models.llm import get_llm
from tutor.prompts import get_level_instructions, render_prompt
from tutor.schemas import ReadingResult
from tutor.state import TutorState
from tutor.utils.markdown_normalizer import normalize_reading_output

logger = logging.getLogger(__name__)


async def reading_node(state: TutorState) -> dict:
    """
    Process text for reading training using Korean slash reading method.

    Uses Claude Sonnet (claude-sonnet-4-5) to generate Korean Markdown
    reading training content with slash reading for each sentence.

    Args:
        state: TutorState containing input_text, level, and supervisor_analysis

    Returns:
        Dictionary with "reading_result" key containing ReadingResult or None on error
    """
    try:
        settings = get_settings()
        llm = get_llm(settings.READING_MODEL, max_tokens=6144)

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
            "reading.md",
            text=input_text,
            level=level,
            level_instructions=level_instructions,
            supervisor_context=supervisor_context,
        )

        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = normalize_reading_output(content)
        return {"reading_result": ReadingResult(content=content)}

    except Exception as e:
        logger.error(f"Error in reading_node: {e}")
        return {"reading_result": None}
