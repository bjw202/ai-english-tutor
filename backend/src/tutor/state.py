"""
LangGraph state management for AI English Tutor.

Defines the TutorState TypedDict for managing workflow state
across the multi-agent LangGraph application.
"""

from __future__ import annotations

from typing import NotRequired, TypedDict

from tutor.schemas import GrammarResult, ReadingResult, VocabularyResult


class TutorState(TypedDict):
    """
    State for the AI English Tutor LangGraph workflow.

    This TypedDict defines the structure of the state object that flows
    through the LangGraph nodes. It includes conversation history,
    analysis results, and task routing information.

    Attributes:
        messages: List of message dictionaries representing conversation history
        level: English proficiency level (1-5, where 1 is beginner, 5 is advanced)
        session_id: Unique session identifier (UUID4 format string)
        input_text: Text content to be analyzed or processed
        reading_result: Optional reading comprehension analysis result
        grammar_result: Optional grammar analysis result
        vocabulary_result: Optional vocabulary analysis result
        extracted_text: Optional OCR-extracted text from image processing
        task_type: Type of task to execute ("analyze" | "image_process" | "chat")
    """

    # Required fields
    messages: list[dict]
    level: int
    session_id: str
    input_text: str
    task_type: str  # "analyze" | "image_process" | "chat"

    # Optional fields (can be None or omitted)
    reading_result: NotRequired[ReadingResult | None]
    grammar_result: NotRequired[GrammarResult | None]
    vocabulary_result: NotRequired[VocabularyResult | None]
    extracted_text: NotRequired[str | None]
