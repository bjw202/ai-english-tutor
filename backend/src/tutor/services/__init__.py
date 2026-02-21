"""Service layer for AI English Tutor.

Provides session management, SSE streaming, and image processing services.
"""

from tutor.services.image import (
    ImageValidationError,
    preprocess_image_for_llm,
    validate_image,
)
from tutor.services.session import SessionManager, session_manager
from tutor.services.streaming import (
    format_done_event,
    format_error_event,
    format_grammar_chunk,
    format_reading_chunk,
    format_sse_event,
    format_vocabulary_chunk,
)

__all__ = [
    # Session management
    "SessionManager",
    "session_manager",
    # SSE streaming
    "format_sse_event",
    "format_reading_chunk",
    "format_grammar_chunk",
    "format_vocabulary_chunk",
    "format_done_event",
    "format_error_event",
    # Image processing
    "validate_image",
    "preprocess_image_for_llm",
    "ImageValidationError",
]
