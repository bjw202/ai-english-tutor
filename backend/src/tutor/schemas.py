"""
Pydantic schemas for request and response validation.

Defines all data models for the AI English Tutor API.
"""

from __future__ import annotations

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


# Supervisor Analysis Schemas (SPEC-UPDATE-001)


class SentenceEntry(BaseModel):
    """Individual sentence entry from supervisor pre-analysis."""

    text: str = Field(..., description="Sentence text")
    difficulty: int = Field(..., ge=1, le=5, description="Difficulty level 1-5")
    focus: list[str] = Field(default_factory=list, description="Learning focus areas")


class SupervisorAnalysis(BaseModel):
    """Supervisor LLM pre-analysis result."""

    sentences: list[SentenceEntry] = Field(default_factory=list)
    overall_difficulty: int = Field(default=3, ge=1, le=5)
    focus_summary: list[str] = Field(default_factory=list)


# Result Schemas (SPEC-UPDATE-001 - content-based Markdown output)


class VocabularyWordEntry(BaseModel):
    """Individual vocabulary word with Korean etymology explanation."""

    word: str = Field(..., description="The vocabulary word")
    content: str = Field(..., description="Korean Markdown explanation (6-step etymology)")


class ReadingResult(BaseModel):
    """Reading training result - Korean Markdown content."""

    content: str = Field(..., description="Korean Markdown with slash reading training")


class GrammarResult(BaseModel):
    """Grammar analysis result - Korean Markdown content."""

    content: str = Field(..., description="Korean Markdown with grammar structure understanding")


class VocabularyResult(BaseModel):
    """Vocabulary etymology result."""

    words: list[VocabularyWordEntry] = Field(default_factory=list)


# Response Schema


class AnalyzeResponse(BaseModel):
    """Aggregated response model for text analysis."""

    session_id: str = Field(..., description="Unique session identifier")
    reading: ReadingResult | None = Field(default=None, description="Reading comprehension result")
    grammar: GrammarResult | None = Field(default=None, description="Grammar analysis result")
    vocabulary: VocabularyResult | None = Field(
        default=None, description="Vocabulary analysis result"
    )
