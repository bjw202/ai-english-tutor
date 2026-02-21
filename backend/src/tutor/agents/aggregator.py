"""
Aggregator agent for combining results.

Collects results from all tutor agents and compiles them
into a unified AnalyzeResponse for the API.
"""

from __future__ import annotations

import logging

from tutor.schemas import AnalyzeResponse
from tutor.state import TutorState

logger = logging.getLogger(__name__)


def aggregator_node(state: TutorState) -> dict:
    """
    Aggregate results from all tutor agents.

    Combines reading, grammar, and vocabulary results into a single
    AnalyzeResponse object. Handles partial results gracefully if some
    agents failed.

    Args:
        state: TutorState containing reading_result, grammar_result, and vocabulary_result

    Returns:
        Dictionary with "analyze_response" key containing AnalyzeResponse
    """
    try:
        # Extract results from state
        session_id = state["session_id"]
        reading_result = state.get("reading_result")
        grammar_result = state.get("grammar_result")
        vocabulary_result = state.get("vocabulary_result")

        # Create aggregated response
        analyze_response = AnalyzeResponse(
            session_id=session_id,
            reading=reading_result,
            grammar=grammar_result,
            vocabulary=vocabulary_result,
        )

        return {"analyze_response": analyze_response}

    except Exception as e:
        logger.error(f"Error in aggregator_node: {e}")
        # Return empty response on error
        return {
            "analyze_response": AnalyzeResponse(
                session_id=state.get("session_id", ""),
                reading=None,
                grammar=None,
                vocabulary=None,
            )
        }
