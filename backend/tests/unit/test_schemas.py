"""Unit tests for Pydantic schemas.

Tests follow TDD approach - defining expected behavior before implementation.
"""

import pytest
from pydantic import ValidationError

from tutor.schemas import (
    AnalyzeImageRequest,
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    GrammarResult,
    ReadingResult,
    VocabularyResult,
    VocabularyWord,
)


class TestAnalyzeRequest:
    """Test AnalyzeRequest schema validation."""

    def test_analyze_request_valid(self):
        """Test valid AnalyzeRequest with minimum text length and valid level."""
        request = AnalyzeRequest(text="This is a valid text for analysis.", level=3)
        assert request.text == "This is a valid text for analysis."
        assert request.level == 3

    def test_analyze_request_minimum_length(self):
        """Test AnalyzeRequest with exactly 10 characters (minimum)."""
        request = AnalyzeRequest(text="1234567890", level=1)
        assert request.text == "1234567890"
        assert len(request.text) == 10

    def test_analyze_request_maximum_length(self):
        """Test AnalyzeRequest with exactly 5000 characters (maximum)."""
        max_text = "a" * 5000
        request = AnalyzeRequest(text=max_text, level=5)
        assert len(request.text) == 5000

    def test_analyze_request_text_too_short(self):
        """Test AnalyzeRequest with text less than 10 characters raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(text="short", level=3)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("text",) and e["type"] == "string_too_short" for e in errors)

    def test_analyze_request_text_too_long(self):
        """Test AnalyzeRequest with text more than 5000 characters raises ValidationError."""
        too_long_text = "a" * 5001

        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(text=too_long_text, level=3)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("text",) and e["type"] == "string_too_long" for e in errors)

    def test_analyze_request_invalid_level_low(self):
        """Test AnalyzeRequest with level 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(text="Valid text input", level=0)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("level",) and e["type"] == "greater_than_equal" for e in errors)

    def test_analyze_request_invalid_level_high(self):
        """Test AnalyzeRequest with level 6 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(text="Valid text input", level=6)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("level",) and e["type"] == "less_than_equal" for e in errors)

    def test_analyze_request_all_valid_levels(self):
        """Test AnalyzeRequest accepts all valid levels (1-5)."""
        for level in [1, 2, 3, 4, 5]:
            request = AnalyzeRequest(text="Valid text for testing.", level=level)
            assert request.level == level

    def test_analyze_request_missing_text(self):
        """Test AnalyzeRequest without text raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(level=3)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("text",) and "missing" in str(e["type"]) for e in errors)

    def test_analyze_request_missing_level(self):
        """Test AnalyzeRequest without level raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(text="Valid text for testing.")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("level",) and "missing" in str(e["type"]) for e in errors)


class TestAnalyzeImageRequest:
    """Test AnalyzeImageRequest schema validation."""

    def test_analyze_image_request_valid(self):
        """Test valid AnalyzeImageRequest with base64 data and valid mime type."""
        image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        request = AnalyzeImageRequest(image_data=image_data, mime_type="image/png", level=2)

        assert request.image_data == image_data
        assert request.mime_type == "image/png"
        assert request.level == 2

    def test_analyze_image_request_valid_mime_types(self):
        """Test AnalyzeImageRequest accepts all valid mime types."""
        image_data = "base64data"

        for mime_type in ["image/jpeg", "image/png", "image/webp"]:
            request = AnalyzeImageRequest(image_data=image_data, mime_type=mime_type, level=1)
            assert request.mime_type == mime_type

    def test_analyze_image_request_invalid_level(self):
        """Test AnalyzeImageRequest with invalid level raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeImageRequest(image_data="data", mime_type="image/png", level=10)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("level",) for e in errors)


class TestChatRequest:
    """Test ChatRequest schema validation."""

    def test_chat_request_valid(self):
        """Test valid ChatRequest with UUID session_id."""
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        request = ChatRequest(
            session_id=session_id, question="What is the past tense of go?", level=2
        )

        assert request.session_id == session_id
        assert request.question == "What is the past tense of go?"
        assert request.level == 2

    def test_chat_request_invalid_level(self):
        """Test ChatRequest with invalid level raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                session_id="550e8400-e29b-41d4-a716-446655440000",
                question="Test question?",
                level=0,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("level",) for e in errors)


class TestReadingResult:
    """Test ReadingResult schema structure."""

    def test_reading_result_structure(self):
        """Test ReadingResult creates valid structure with all fields."""
        result = ReadingResult(
            summary="The text discusses climate change effects.",
            main_topic="Climate Change",
            emotional_tone="concerned",
        )

        assert result.summary == "The text discusses climate change effects."
        assert result.main_topic == "Climate Change"
        assert result.emotional_tone == "concerned"

    def test_reading_result_serialization(self):
        """Test ReadingResult can be serialized to JSON."""
        result = ReadingResult(
            summary="Test summary", main_topic="Test Topic", emotional_tone="neutral"
        )

        data = result.model_dump()

        assert data == {
            "summary": "Test summary",
            "main_topic": "Test Topic",
            "emotional_tone": "neutral",
        }


class TestGrammarResult:
    """Test GrammarResult schema structure."""

    def test_grammar_result_structure(self):
        """Test GrammarResult creates valid structure with all fields."""
        result = GrammarResult(
            tenses=["present simple", "past simple"],
            voice="active",
            sentence_structure="compound",
            analysis="The text uses simple sentence structures with clear tense usage.",
        )

        assert result.tenses == ["present simple", "past simple"]
        assert result.voice == "active"
        assert result.sentence_structure == "compound"
        assert result.analysis == "The text uses simple sentence structures with clear tense usage."

    def test_grammar_result_empty_tenses(self):
        """Test GrammarResult accepts empty tenses list."""
        result = GrammarResult(
            tenses=[], voice="active", sentence_structure="simple", analysis="No tenses found."
        )

        assert result.tenses == []

    def test_grammar_result_serialization(self):
        """Test GrammarResult can be serialized to JSON."""
        result = GrammarResult(
            tenses=["present perfect"],
            voice="passive",
            sentence_structure="complex",
            analysis="Test",
        )

        data = result.model_dump()

        assert data == {
            "tenses": ["present perfect"],
            "voice": "passive",
            "sentence_structure": "complex",
            "analysis": "Test",
        }


class TestVocabularyResult:
    """Test VocabularyResult schema structure."""

    def test_vocabulary_result_word_list(self):
        """Test VocabularyResult with multiple vocabulary words."""
        words = [
            VocabularyWord(
                term="ephemeral",
                meaning="lasting for a very short time",
                usage="The ephemeral beauty of cherry blossoms.",
                synonyms=["transient", "fleeting", "short-lived"],
            ),
            VocabularyWord(
                term="ubiquitous",
                meaning="present, appearing, or found everywhere",
                usage="Smartphones have become ubiquitous in modern society.",
                synonyms=["omnipresent", "pervasive", "universal"],
            ),
        ]

        result = VocabularyResult(words=words)

        assert len(result.words) == 2
        assert result.words[0].term == "ephemeral"
        assert result.words[1].term == "ubiquitous"
        assert result.words[0].synonyms == ["transient", "fleeting", "short-lived"]

    def test_vocabulary_result_empty_list(self):
        """Test VocabularyResult with empty word list."""
        result = VocabularyResult(words=[])

        assert result.words == []

    def test_vocabulary_word_structure(self):
        """Test VocabularyWord has all required fields."""
        word = VocabularyWord(
            term="test",
            meaning="a procedure intended to establish the quality",
            usage="This is a test.",
            synonyms=["examination", "trial", "experiment"],
        )

        assert word.term == "test"
        assert word.meaning == "a procedure intended to establish the quality"
        assert word.usage == "This is a test."
        assert word.synonyms == ["examination", "trial", "experiment"]

    def test_vocabulary_word_empty_synonyms(self):
        """Test VocabularyWord accepts empty synonyms list."""
        word = VocabularyWord(
            term="unique",
            meaning="being the only one of its kind",
            usage="This is unique.",
            synonyms=[],
        )

        assert word.synonyms == []


class TestAnalyzeResponse:
    """Test AnalyzeResponse schema aggregation."""

    def test_analyze_response_with_all_results(self):
        """Test AnalyzeResponse aggregates all three tutor results."""
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        reading = ReadingResult(summary="Test", main_topic="Topic", emotional_tone="neutral")
        grammar = GrammarResult(
            tenses=["present"], voice="active", sentence_structure="simple", analysis="Good"
        )
        vocabulary = VocabularyResult(
            words=[VocabularyWord(term="test", meaning="test", usage="test", synonyms=["synonym"])]
        )

        response = AnalyzeResponse(
            session_id=session_id, reading=reading, grammar=grammar, vocabulary=vocabulary
        )

        assert response.session_id == session_id
        assert response.reading.summary == "Test"
        assert response.grammar.tenses == ["present"]
        assert response.vocabulary.words[0].term == "test"

    def test_analyze_response_with_partial_results(self):
        """Test AnalyzeResponse accepts partial results (None values)."""
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        reading = ReadingResult(summary="Test", main_topic="Topic", emotional_tone="neutral")

        response = AnalyzeResponse(session_id=session_id, reading=reading)

        assert response.session_id == session_id
        assert response.reading is not None
        assert response.grammar is None
        assert response.vocabulary is None

    def test_analyze_response_with_no_results(self):
        """Test AnalyzeResponse with all result fields as None."""
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = AnalyzeResponse(session_id=session_id)

        assert response.session_id == session_id
        assert response.reading is None
        assert response.grammar is None
        assert response.vocabulary is None

    def test_analyze_response_serialization(self):
        """Test AnalyzeResponse can be serialized to JSON."""
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        reading = ReadingResult(summary="Test", main_topic="Topic", emotional_tone="neutral")

        response = AnalyzeResponse(session_id=session_id, reading=reading)
        data = response.model_dump()

        assert "session_id" in data
        assert "reading" in data
        assert data["reading"]["summary"] == "Test"
