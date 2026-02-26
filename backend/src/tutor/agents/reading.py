"""
Reading training agent - Korean slash reading method.

Uses Claude Sonnet to generate Korean Markdown reading training content
including slash reading (직독직해) for each sentence.
"""

from __future__ import annotations

import asyncio
import logging

from tutor.config import get_settings
from tutor.models.llm import get_llm
from tutor.prompts import get_level_instructions, render_prompt
from tutor.schemas import ReadingResult
from tutor.state import TutorState
from tutor.utils.markdown_normalizer import normalize_reading_output

logger = logging.getLogger(__name__)


async def reading_node(state: TutorState, token_queue: asyncio.Queue | None = None) -> dict:
    """
    Process text for reading training using Korean slash reading method.

    Uses Claude Sonnet (claude-sonnet-4-5) to generate Korean Markdown
    reading training content with slash reading for each sentence.

    Args:
        state: TutorState containing input_text, level, and supervisor_analysis
        token_queue: Optional asyncio.Queue to stream tokens to the router.
            Each token is put as a string. A None sentinel is put when streaming
            completes (or on error) to signal the consumer to stop reading.

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

        accumulated = ""
        async for chunk in llm.astream(prompt):
            raw = chunk.content if hasattr(chunk, "content") else ""
            if not isinstance(raw, str):
                continue
            token = raw
            if token:
                accumulated += token
                if token_queue is not None:
                    await token_queue.put(token)

        if token_queue is not None:
            await token_queue.put(None)  # sentinel: streaming complete

        content = normalize_reading_output(accumulated)
        return {"reading_result": ReadingResult(content=content)}

    except Exception as e:
        logger.error(f"Error in reading_node: {e}")
        if token_queue is not None:
            await token_queue.put(None)  # sentinel: ensure consumer loop exits
        return {
            "reading_result": None,
            "reading_error": str(e),
        }
