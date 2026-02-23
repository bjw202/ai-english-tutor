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
    SentenceEntry,
    SupervisorAnalysis,
    VocabularyResult,
    VocabularyWordEntry,
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


class TestSentenceEntry:
    """Test SentenceEntry schema for supervisor pre-analysis."""

    def test_sentence_entry_valid(self):
        """Test valid SentenceEntry with all fields."""
        entry = SentenceEntry(
            text="The quick brown fox jumps over the lazy dog.",
            difficulty=3,
            focus=["reading", "vocabulary"],
        )
        assert entry.text == "The quick brown fox jumps over the lazy dog."
        assert entry.difficulty == 3
        assert entry.focus == ["reading", "vocabulary"]

    def test_sentence_entry_default_focus(self):
        """Test SentenceEntry has empty focus list by default."""
        entry = SentenceEntry(text="Test sentence.", difficulty=2)
        assert entry.focus == []

    def test_sentence_entry_difficulty_range(self):
        """Test SentenceEntry validates difficulty range 1-5."""
        for difficulty in [1, 2, 3, 4, 5]:
            entry = SentenceEntry(text="Test.", difficulty=difficulty)
            assert entry.difficulty == difficulty

    def test_sentence_entry_invalid_difficulty_low(self):
        """Test SentenceEntry rejects difficulty below 1."""
        with pytest.raises(ValidationError):
            SentenceEntry(text="Test.", difficulty=0)

    def test_sentence_entry_invalid_difficulty_high(self):
        """Test SentenceEntry rejects difficulty above 5."""
        with pytest.raises(ValidationError):
            SentenceEntry(text="Test.", difficulty=6)


class TestSupervisorAnalysis:
    """Test SupervisorAnalysis schema for supervisor pre-analysis results."""

    def test_supervisor_analysis_valid(self):
        """Test valid SupervisorAnalysis with all fields."""
        sentences = [
            SentenceEntry(text="First sentence.", difficulty=2, focus=["reading"]),
            SentenceEntry(text="Second sentence.", difficulty=4, focus=["grammar"]),
        ]
        analysis = SupervisorAnalysis(
            sentences=sentences,
            overall_difficulty=3,
            focus_summary=["grammar", "reading"],
        )
        assert len(analysis.sentences) == 2
        assert analysis.overall_difficulty == 3
        assert analysis.focus_summary == ["grammar", "reading"]

    def test_supervisor_analysis_defaults(self):
        """Test SupervisorAnalysis has appropriate defaults."""
        analysis = SupervisorAnalysis()
        assert analysis.sentences == []
        assert analysis.overall_difficulty == 3
        assert analysis.focus_summary == []

    def test_supervisor_analysis_overall_difficulty_range(self):
        """Test SupervisorAnalysis validates overall_difficulty range 1-5."""
        for difficulty in [1, 2, 3, 4, 5]:
            analysis = SupervisorAnalysis(overall_difficulty=difficulty)
            assert analysis.overall_difficulty == difficulty

    def test_supervisor_analysis_invalid_difficulty(self):
        """Test SupervisorAnalysis rejects invalid overall_difficulty."""
        with pytest.raises(ValidationError):
            SupervisorAnalysis(overall_difficulty=0)
        with pytest.raises(ValidationError):
            SupervisorAnalysis(overall_difficulty=6)


class TestReadingResult:
    """Test ReadingResult schema structure (content-based, SPEC-UPDATE-001)."""

    def test_reading_result_structure(self):
        """Test ReadingResult creates valid structure with content field."""
        result = ReadingResult(
            content="## 문장 분석\n\nThe quick brown fox / jumps / over the lazy dog.\n\n..."
        )
        assert "문장 분석" in result.content

    def test_reading_result_serialization(self):
        """Test ReadingResult can be serialized to JSON."""
        result = ReadingResult(content="Korean Markdown reading content here.")

        data = result.model_dump()

        assert data == {"content": "Korean Markdown reading content here."}

    def test_reading_result_missing_content(self):
        """Test ReadingResult raises ValidationError without content."""
        with pytest.raises(ValidationError):
            ReadingResult()


class TestGrammarResult:
    """Test GrammarResult schema structure (content-based, SPEC-UPDATE-001)."""

    def test_grammar_result_structure(self):
        """Test GrammarResult creates valid structure with content field."""
        result = GrammarResult(
            content="## 문법 분석\n\n**문법 포인트**: 현재완료..."
        )
        assert "문법 분석" in result.content

    def test_grammar_result_serialization(self):
        """Test GrammarResult can be serialized to JSON."""
        result = GrammarResult(content="Korean Markdown grammar content here.")

        data = result.model_dump()

        assert data == {"content": "Korean Markdown grammar content here."}

    def test_grammar_result_missing_content(self):
        """Test GrammarResult raises ValidationError without content."""
        with pytest.raises(ValidationError):
            GrammarResult()


class TestVocabularyWordEntry:
    """Test VocabularyWordEntry schema structure (SPEC-UPDATE-001)."""

    def test_vocabulary_word_entry_valid(self):
        """Test VocabularyWordEntry has word and content fields."""
        entry = VocabularyWordEntry(
            word="ephemeral",
            content="### 1. 기본 뜻\n짧은 시간 동안만 지속되는\n\n### 2. 문장 속 의미\n...",
        )
        assert entry.word == "ephemeral"
        assert "기본 뜻" in entry.content

    def test_vocabulary_word_entry_serialization(self):
        """Test VocabularyWordEntry can be serialized to JSON."""
        entry = VocabularyWordEntry(word="test", content="Test content")
        data = entry.model_dump()
        assert data == {"word": "test", "content": "Test content"}

    def test_vocabulary_word_entry_missing_fields(self):
        """Test VocabularyWordEntry raises ValidationError without required fields."""
        with pytest.raises(ValidationError):
            VocabularyWordEntry(word="test")  # missing content
        with pytest.raises(ValidationError):
            VocabularyWordEntry(content="content")  # missing word


class TestVocabularyResult:
    """Test VocabularyResult schema structure."""

    def test_vocabulary_result_word_list(self):
        """Test VocabularyResult with multiple vocabulary word entries."""
        words = [
            VocabularyWordEntry(word="ephemeral", content="Korean etymology content for ephemeral"),
            VocabularyWordEntry(word="ubiquitous", content="Korean etymology content for ubiquitous"),
        ]

        result = VocabularyResult(words=words)

        assert len(result.words) == 2
        assert result.words[0].word == "ephemeral"
        assert result.words[1].word == "ubiquitous"

    def test_vocabulary_result_empty_list(self):
        """Test VocabularyResult with empty word list."""
        result = VocabularyResult(words=[])

        assert result.words == []

    def test_vocabulary_result_serialization(self):
        """Test VocabularyResult can be serialized to JSON."""
        result = VocabularyResult(
            words=[VocabularyWordEntry(word="test", content="Test content")]
        )
        data = result.model_dump()
        assert data == {"words": [{"word": "test", "content": "Test content"}]}


class TestAnalyzeResponse:
    """Test AnalyzeResponse schema aggregation."""

    def test_analyze_response_with_all_results(self):
        """Test AnalyzeResponse aggregates all three tutor results."""
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        reading = ReadingResult(content="Reading Korean Markdown content")
        grammar = GrammarResult(content="Grammar Korean Markdown content")
        vocabulary = VocabularyResult(
            words=[VocabularyWordEntry(word="test", content="Test etymology content")]
        )

        response = AnalyzeResponse(
            session_id=session_id, reading=reading, grammar=grammar, vocabulary=vocabulary
        )

        assert response.session_id == session_id
        assert response.reading.content == "Reading Korean Markdown content"
        assert response.grammar.content == "Grammar Korean Markdown content"
        assert response.vocabulary.words[0].word == "test"

    def test_analyze_response_with_partial_results(self):
        """Test AnalyzeResponse accepts partial results (None values)."""
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        reading = ReadingResult(content="Reading content")

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
        reading = ReadingResult(content="Reading content")

        response = AnalyzeResponse(session_id=session_id, reading=reading)
        data = response.model_dump()

        assert "session_id" in data
        assert "reading" in data
        assert data["reading"]["content"] == "Reading content"
