"""
Pydantic schemas for request and response validation.

Defines all data models for the AI English Tutor API.
"""

from typing import Literal

from pydantic import BaseModel, Field

# Request Schemas


class AnalyzeRequest(BaseModel):
    """Request model for text analysis endpoint."""

    text: str = Field(..., min_length=10, max_length=5000, description="Text content to analyze")
    level: int = Field(..., ge=1, le=5, description="English proficiency level (1-5)")


class AnalyzeImageRequest(BaseModel):
    """Request model for image analysis endpoint."""

    image_data: str = Field(..., description="Base64 encoded image data")
    mime_type: Literal["image/jpeg", "image/png", "image/webp"] = Field(
        ..., description="Image MIME type"
    )
    level: int = Field(..., ge=1, le=5, description="English proficiency level (1-5)")


class ChatRequest(BaseModel):
    """Request model for chat conversation endpoint."""

    session_id: str = Field(..., description="Unique session identifier")
    question: str = Field(..., description="User question")
    level: int = Field(..., ge=1, le=5, description="English proficiency level (1-5)")


# Result Schemas


class ReadingResult(BaseModel):
    """Result model for reading comprehension analysis."""

    summary: str = Field(..., description="Summary of the text")
    main_topic: str = Field(..., description="Main topic of the text")
    emotional_tone: str = Field(..., description="Emotional tone detected in the text")


class GrammarResult(BaseModel):
    """Result model for grammar analysis."""

    tenses: list[str] = Field(default_factory=list, description="List of tenses used in the text")
    voice: str = Field(..., description="Voice used (active/passive)")
    sentence_structure: str = Field(..., description="Sentence structure type")
    analysis: str = Field(..., description="Detailed grammar analysis")


class VocabularyWord(BaseModel):
    """Single vocabulary word entry."""

    term: str = Field(..., description="The vocabulary word")
    meaning: str = Field(..., description="Definition of the word")
    usage: str = Field(..., description="Example usage sentence")
    synonyms: list[str] = Field(default_factory=list, description="List of synonyms")


class VocabularyResult(BaseModel):
    """Result model for vocabulary analysis."""

    words: list[VocabularyWord] = Field(
        default_factory=list, description="List of vocabulary words"
    )


# Response Schema


class AnalyzeResponse(BaseModel):
    """Aggregated response model for text analysis."""

    session_id: str = Field(..., description="Unique session identifier")
    reading: ReadingResult | None = Field(default=None, description="Reading comprehension result")
    grammar: GrammarResult | None = Field(default=None, description="Grammar analysis result")
    vocabulary: VocabularyResult | None = Field(
        default=None, description="Vocabulary analysis result"
    )
