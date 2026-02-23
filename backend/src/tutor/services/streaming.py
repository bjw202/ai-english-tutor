"""Server-Sent Events (SSE) streaming service for AI English Tutor.

Formats LangGraph output as SSE events for real-time streaming.
"""

import json
from typing import Any


def format_sse_event(event_type: str, data: dict[str, Any]) -> str:
    """Format data as SSE event string.

    Args:
        event_type: The SSE event type (e.g., "reading_chunk", "error")
        data: The data payload to include in the event

    Returns:
        A formatted SSE event string

    Example:
        >>> format_sse_event("message", {"text": "hello"})
        'event: message\\ndata: {"text": "hello"}\\n\\n'
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def format_reading_chunk(data: dict) -> str:
    """Format reading comprehension result as SSE event.

    Args:
        data: Reading comprehension result data

    Returns:
        A formatted SSE event with event_type="reading_chunk"
    """
    return format_sse_event("reading_chunk", data)


def format_grammar_chunk(data: dict) -> str:
    """Format grammar analysis result as SSE event.

    Args:
        data: Grammar analysis result data

    Returns:
        A formatted SSE event with event_type="grammar_chunk"
    """
    return format_sse_event("grammar_chunk", data)


def format_vocabulary_chunk(data: dict) -> str:
    """Format vocabulary analysis result as SSE event.

    Args:
        data: Vocabulary analysis result data

    Returns:
        A formatted SSE event with event_type="vocabulary_chunk"
    """
    return format_sse_event("vocabulary_chunk", data)


def format_done_event(session_id: str) -> str:
    """Format completion event as SSE event.

    Args:
        session_id: The completed session ID

    Returns:
        A formatted SSE event with event_type="done"
    """
    return format_sse_event("done", {"session_id": session_id, "status": "complete"})


def format_error_event(message: str, code: str = "error") -> str:
    """Format error event as SSE event.

    Args:
        message: The error message
        code: The error code (default: "error")

    Returns:
        A formatted SSE event with event_type="error"
    """
    return format_sse_event("error", {"message": message, "code": code})


def format_reading_token(token: str) -> str:
    """Format a single reading token as SSE event.

    Args:
        token: A single token string from the reading agent LLM stream

    Returns:
        A formatted SSE event with event_type="reading_token"
    """
    return format_sse_event("reading_token", {"token": token})


def format_grammar_token(token: str) -> str:
    """Format a single grammar token as SSE event.

    Args:
        token: A single token string from the grammar agent LLM stream

    Returns:
        A formatted SSE event with event_type="grammar_token"
    """
    return format_sse_event("grammar_token", {"token": token})


def format_section_done(section: str) -> str:
    """Format section completion as SSE event.

    Args:
        section: The section name that completed (e.g., "reading", "grammar")

    Returns:
        A formatted SSE event with event_type="{section}_done"
    """
    return format_sse_event(f"{section}_done", {"section": section})
