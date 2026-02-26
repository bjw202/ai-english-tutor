"""
Vocabulary etymology agent - Korean etymology network-based explanation.

Uses Claude Sonnet (upgraded from Haiku) to generate Korean Markdown
vocabulary content with 6-step etymology explanation for each word.
"""

from __future__ import annotations

import asyncio
import logging
import re

from tutor.config import get_settings
from tutor.models.llm import get_llm
from tutor.prompts import get_level_instructions, render_prompt
from tutor.schemas import VocabularyResult, VocabularyWordEntry
from tutor.state import TutorState
from tutor.utils.markdown_normalizer import normalize_vocabulary_output

logger = logging.getLogger(__name__)


def _parse_vocabulary_words(content: str) -> list[VocabularyWordEntry]:
    """Parse vocabulary word entries from Markdown output.

    The vocabulary prompt instructs the LLM to output sections like:
        ## word1
        ...content...
        ---
        ## word2
        ...content...

    Parses by splitting on '## ' headers to extract individual word entries.

    Args:
        content: Raw Markdown text from the LLM

    Returns:
        List of VocabularyWordEntry instances
    """
    words = []

    # Split on markdown h2 headers (## word)
    # Use regex to split on lines starting with ## followed by non-# character
    parts = re.split(r"\n## ", content)

    for part in parts:
        # Skip empty parts and the leading section before first ##
        if not part.strip():
            continue

        # Check if this looks like a word entry (not the footer/instructions section)
        lines = part.strip().split("\n")
        if not lines:
            continue

        # First line is the word (or "## word" if it's the very first part)
        word_line = lines[0].strip()

        # Skip if it looks like an instruction section (e.g., "절대 금지")
        if "금지" in word_line or "원칙" in word_line or "형식" in word_line:
            continue

        # Extract the word - remove any leading ## if present
        word = word_line.lstrip("#").strip()

        # Strip trailing section separators from content
        word_content = part
        # Remove the word from the content header if it starts with the word
        if word_content.startswith(word_line):
            word_content = word_content[len(word_line):].strip()

        # Remove trailing --- separators
        word_content = word_content.rstrip("-").strip()

        if word and word_content:
            words.append(VocabularyWordEntry(word=word, content=word_content))

    logger.info(f"Parsed {len(words)} vocabulary words from Markdown output")
    return words


async def vocabulary_node(state: TutorState, token_queue: asyncio.Queue | None = None) -> dict:
    """
    Process text for vocabulary etymology explanation.

    Uses Claude Sonnet (claude-sonnet-4-5) to analyze the input text
    and generate Korean Markdown vocabulary content with 6-step
    etymology explanation for each selected word.

    Model upgraded from claude-haiku-4-5 to claude-sonnet-4-5 for better
    Korean etymology quality.

    Args:
        state: TutorState containing input_text, level, and supervisor_analysis
        token_queue: Optional asyncio.Queue to stream tokens to the router.
            Each token is put as a string. A None sentinel is put when streaming
            completes (or on error) to signal the consumer to stop reading.

    Returns:
        Dictionary with "vocabulary_result" key containing VocabularyResult
    """
    settings = get_settings()
    llm = get_llm(settings.VOCABULARY_MODEL, max_tokens=6144)

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
        "vocabulary.md",
        text=input_text,
        level=level,
        level_instructions=level_instructions,
        supervisor_context=supervisor_context,
    )

    try:
        accumulated = ""
        async for chunk in llm.astream(prompt):
            raw = chunk.content if hasattr(chunk, "content") else ""
            if not isinstance(raw, str):
                continue  # skip non-text chunks (multimodal/tool-use)
            token = raw
            if token:
                accumulated += token
                if token_queue is not None:
                    await token_queue.put(token)

        if token_queue is not None:
            await token_queue.put(None)  # sentinel: streaming complete

        content = normalize_vocabulary_output(accumulated)
        words = _parse_vocabulary_words(content)
        return {"vocabulary_result": VocabularyResult(words=words)}
    except Exception as e:
        logger.error(f"Error in vocabulary_node: {e}")
        if token_queue is not None:
            await token_queue.put(None)  # sentinel: ensure consumer loop exits on error
        return {
            "vocabulary_result": VocabularyResult(words=[]),
            "vocabulary_error": str(e),
        }
