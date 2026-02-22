"""
Vocabulary extraction agent.

Uses Claude Haiku to extract vocabulary words from text including:
- Word terms
- Definitions
- Usage examples
- Synonyms
"""

from __future__ import annotations

import json
import logging

from tutor.models.llm import get_llm
from tutor.prompts import get_level_instructions, render_prompt
from tutor.schemas import VocabularyResult, VocabularyWord
from tutor.state import TutorState

logger = logging.getLogger(__name__)


async def _parse_vocabulary_from_raw(content: str) -> VocabularyResult:
    """Parse vocabulary result from raw LLM text response.

    Attempts to extract JSON from the response text and parse it into
    a VocabularyResult. Returns an empty result if parsing fails.

    Args:
        content: Raw text response from the LLM

    Returns:
        VocabularyResult with parsed words, or empty result on failure
    """
    try:
        # Try to find JSON object in the response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            logger.warning("No JSON object found in raw LLM response")
            return VocabularyResult(words=[])

        json_str = content[start:end]
        data = json.loads(json_str)

        words_data = data.get("words", [])
        words = []
        for w in words_data:
            if isinstance(w, dict) and "term" in w and "meaning" in w:
                words.append(
                    VocabularyWord(
                        term=w.get("term", ""),
                        meaning=w.get("meaning", ""),
                        usage=w.get("usage", ""),
                        synonyms=w.get("synonyms", []),
                    )
                )

        logger.info(f"Fallback parser extracted {len(words)} words from raw response")
        return VocabularyResult(words=words)

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse raw vocabulary response: {e}")
        return VocabularyResult(words=[])


async def vocabulary_node(state: TutorState) -> dict:
    """
    Process text for vocabulary extraction.

    Uses Claude Haiku (claude-haiku-4-5) to analyze the input text
    and extract vocabulary words with definitions, usage examples, and synonyms.

    Attempts structured output first. If that fails, falls back to raw LLM
    invocation with manual JSON parsing. Always returns a VocabularyResult
    (never None) so the frontend receives the vocabulary_chunk SSE event.

    Args:
        state: TutorState containing input_text and level

    Returns:
        Dictionary with "vocabulary_result" key containing VocabularyResult
    """
    llm = get_llm("claude-haiku-4-5")

    level = state.get("level", 3)
    input_text = state.get("input_text", "")

    level_instructions = get_level_instructions(level)

    prompt = render_prompt(
        "vocabulary.md",
        text=input_text,
        level=level,
        level_instructions=level_instructions,
    )

    json_instruction = (
        '\n\nIMPORTANT: You must respond with a valid JSON object containing a "words" array. '
        'Each word in the array must have "term", "meaning", "usage", and "synonyms" fields.'
    )
    full_prompt = prompt + json_instruction

    # Attempt 1: structured output
    try:
        structured_llm = llm.with_structured_output(VocabularyResult)
        vocabulary_result = await structured_llm.ainvoke(full_prompt)

        if vocabulary_result is None:
            logger.warning("Structured output returned None, falling back to raw invocation")
            raise ValueError("Structured output returned None")

        logger.info(f"Vocabulary result extracted (structured): {len(vocabulary_result.words)} words")
        return {"vocabulary_result": vocabulary_result}

    except Exception as e:
        logger.warning(f"Structured output failed, attempting raw fallback: {e}")

    # Attempt 2: raw LLM invocation with manual JSON parsing
    try:
        raw_response = await llm.ainvoke(full_prompt)
        content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
        vocabulary_result = await _parse_vocabulary_from_raw(content)
        logger.info(f"Vocabulary result extracted (raw fallback): {len(vocabulary_result.words)} words")
        return {"vocabulary_result": vocabulary_result}

    except Exception as e:
        logger.error(f"Raw fallback also failed in vocabulary_node: {e}", exc_info=True)
        return {"vocabulary_result": VocabularyResult(words=[])}
