"""
Unit tests for AI English Tutor agents.

Tests all agent nodes for the LangGraph workflow including:
- Supervisor: LLM-powered pre-analyzer (SPEC-UPDATE-001)
- Reading: Reading training with Korean slash reading method
- Grammar: Grammar explanation with Korean structure analysis
- Vocabulary: Vocabulary etymology with Korean explanation (upgraded to Sonnet)
- ImageProcessor: Text extraction from images
- Aggregator: Combines all tutor agent results

All tests use mocked LLM responses to avoid actual API calls.
"""

from __future__ import annotations

import base64
import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tutor.schemas import (
    AnalyzeResponse,
    GrammarResult,
    ReadingResult,
    SentenceEntry,
    SupervisorAnalysis,
    VocabularyResult,
    VocabularyWordEntry,
)
from tutor.state import TutorState


class TestSupervisorAgent:
    """Test cases for the supervisor LLM pre-analyzer agent."""

    @pytest.fixture
    def base_state(self) -> TutorState:
        """Create a base TutorState for testing."""
        return {
            "messages": [],
            "level": 3,
            "session_id": "test-session-123",
            "input_text": "Hello, world! This is a test sentence.",
            "task_type": "analyze",
        }

    @pytest.mark.asyncio
    async def test_supervisor_returns_analysis_for_analyze_task(
        self, base_state: TutorState
    ) -> None:
        """
        GIVEN a state with task_type='analyze' and input_text
        WHEN supervisor_node is called
        THEN it should return supervisor_analysis with sentences and difficulty
        """
        from tutor.agents.supervisor import supervisor_node

        # Mock LLM JSON response
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "sentences": [
                {"text": "Hello, world!", "difficulty": 2, "focus": ["reading"]},
                {"text": "This is a test sentence.", "difficulty": 2, "focus": ["grammar"]},
            ],
            "overall_difficulty": 2,
            "focus_summary": ["reading", "grammar"],
        })

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("tutor.agents.supervisor.get_llm", return_value=mock_llm):
            result = await supervisor_node(base_state)

        assert "supervisor_analysis" in result
        analysis = result["supervisor_analysis"]
        assert isinstance(analysis, SupervisorAnalysis)
        assert len(analysis.sentences) == 2
        assert analysis.overall_difficulty == 2
        assert "reading" in analysis.focus_summary

    @pytest.mark.asyncio
    async def test_supervisor_uses_config_model(self, base_state: TutorState) -> None:
        """
        GIVEN a state with task_type='analyze'
        WHEN supervisor_node is called
        THEN it should use SUPERVISOR_MODEL from config (R1, R2)
        """
        from tutor.agents.supervisor import supervisor_node

        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "sentences": [{"text": "Test.", "difficulty": 3, "focus": ["reading"]}],
            "overall_difficulty": 3,
            "focus_summary": ["reading"],
        })

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPERVISOR_MODEL = "gpt-4o-mini"

        with patch("tutor.agents.supervisor.get_llm", return_value=mock_llm) as mock_get_llm, \
             patch("tutor.agents.supervisor.get_settings", return_value=mock_settings_obj):
            await supervisor_node(base_state)

            mock_get_llm.assert_called_once_with(
                mock_settings_obj.SUPERVISOR_MODEL, max_tokens=1024, timeout=30
            )

    @pytest.mark.asyncio
    async def test_supervisor_skips_non_analyze_tasks(self, base_state: TutorState) -> None:
        """
        GIVEN a state with task_type='chat'
        WHEN supervisor_node is called
        THEN it should return empty dict (skip pre-analysis)
        """
        from tutor.agents.supervisor import supervisor_node

        base_state["task_type"] = "chat"

        with patch("tutor.agents.supervisor.get_llm") as mock_get_llm:
            result = await supervisor_node(base_state)

        # Should skip pre-analysis and not call the LLM
        assert result == {}
        mock_get_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_supervisor_skips_empty_input_text(self, base_state: TutorState) -> None:
        """
        GIVEN a state with empty input_text
        WHEN supervisor_node is called
        THEN it should return empty dict (skip pre-analysis)
        """
        from tutor.agents.supervisor import supervisor_node

        base_state["input_text"] = ""

        with patch("tutor.agents.supervisor.get_llm") as mock_get_llm:
            result = await supervisor_node(base_state)

        assert result == {}
        mock_get_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_supervisor_falls_back_on_llm_failure(self, base_state: TutorState) -> None:
        """
        GIVEN a state with valid input_text
        WHEN supervisor LLM fails
        THEN it should fall back to basic sentence splitting
        """
        from tutor.agents.supervisor import supervisor_node

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("LLM API error")

        with patch("tutor.agents.supervisor.get_llm", return_value=mock_llm):
            result = await supervisor_node(base_state)

        assert "supervisor_analysis" in result
        analysis = result["supervisor_analysis"]
        assert isinstance(analysis, SupervisorAnalysis)
        # Fallback should still produce sentences
        assert len(analysis.sentences) >= 0

    @pytest.mark.asyncio
    async def test_supervisor_falls_back_on_invalid_json(self, base_state: TutorState) -> None:
        """
        GIVEN a state with valid input_text
        WHEN supervisor LLM returns invalid JSON
        THEN it should fall back to basic sentence splitting
        """
        from tutor.agents.supervisor import supervisor_node

        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON at all!"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("tutor.agents.supervisor.get_llm", return_value=mock_llm):
            result = await supervisor_node(base_state)

        assert "supervisor_analysis" in result
        analysis = result["supervisor_analysis"]
        assert isinstance(analysis, SupervisorAnalysis)


class TestReadingAgent:
    """Test cases for the reading comprehension agent (SPEC-UPDATE-001)."""

    @pytest.fixture
    def reading_state(self) -> TutorState:
        """Create a TutorState for reading agent testing."""
        return {
            "messages": [],
            "level": 3,
            "session_id": "test-session-123",
            "input_text": "The quick brown fox jumps over the lazy dog.",
            "task_type": "analyze",
        }

    @pytest.mark.asyncio
    async def test_reading_agent_returns_reading_result(
        self, reading_state: TutorState
    ) -> None:
        """
        GIVEN a state with input_text and level
        WHEN reading_node is called
        THEN it should return a ReadingResult with Korean Markdown content
        """
        from tutor.agents.reading import reading_node

        # Mock raw LLM response (not structured output)
        mock_response = MagicMock()
        mock_response.content = "## 슬래시 직독\n\nThe quick brown fox / jumps / over the lazy dog.\n\n..."

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("tutor.agents.reading.get_llm", return_value=mock_llm), \
             patch("tutor.agents.reading.render_prompt", return_value="Test prompt"):
            result = await reading_node(reading_state)

        assert "reading_result" in result
        reading_result = result["reading_result"]
        assert isinstance(reading_result, ReadingResult)
        assert "슬래시 직독" in reading_result.content

    @pytest.mark.asyncio
    async def test_reading_agent_uses_config_model(
        self, reading_state: TutorState
    ) -> None:
        """
        GIVEN a reading analysis request
        WHEN reading_node is called
        THEN it should use READING_MODEL from config with max_tokens=6144 (R1, R2, R7)
        """
        from tutor.agents.reading import reading_node

        mock_response = MagicMock()
        mock_response.content = "Korean Markdown reading content"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        mock_settings_obj = MagicMock()
        mock_settings_obj.READING_MODEL = "gpt-4o-mini"

        with patch("tutor.agents.reading.get_llm", return_value=mock_llm) as mock_get_llm, \
             patch("tutor.agents.reading.get_settings", return_value=mock_settings_obj):
            await reading_node(reading_state)

            mock_get_llm.assert_called_once_with(
                mock_settings_obj.READING_MODEL, max_tokens=6144
            )

    @pytest.mark.asyncio
    async def test_reading_agent_uses_raw_llm_invocation(
        self, reading_state: TutorState
    ) -> None:
        """
        GIVEN a reading analysis request
        WHEN reading_node is called
        THEN it should use raw llm.ainvoke() (not with_structured_output)
        """
        from tutor.agents.reading import reading_node

        mock_response = MagicMock()
        mock_response.content = "Reading content"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("tutor.agents.reading.get_llm", return_value=mock_llm), \
             patch("tutor.agents.reading.render_prompt", return_value="Test prompt"):
            await reading_node(reading_state)

        # Should use ainvoke directly, not with_structured_output
        mock_llm.ainvoke.assert_called_once()
        mock_llm.with_structured_output.assert_not_called()

    @pytest.mark.asyncio
    async def test_reading_agent_includes_supervisor_context(
        self, reading_state: TutorState
    ) -> None:
        """
        GIVEN a state with supervisor_analysis
        WHEN reading_node is called
        THEN it should include supervisor context in the prompt
        """
        from tutor.agents.reading import reading_node

        reading_state["supervisor_analysis"] = SupervisorAnalysis(
            sentences=[SentenceEntry(text="Test.", difficulty=3, focus=["reading"])],
            overall_difficulty=3,
            focus_summary=["reading", "grammar"],
        )

        mock_response = MagicMock()
        mock_response.content = "Reading content"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        captured_prompt = {}

        def capture_render_prompt(name, **kwargs):
            captured_prompt.update(kwargs)
            return "Test prompt"

        with patch("tutor.agents.reading.get_llm", return_value=mock_llm), \
             patch("tutor.agents.reading.render_prompt", side_effect=capture_render_prompt):
            await reading_node(reading_state)

        # Supervisor context should be included in prompt kwargs
        assert "supervisor_context" in captured_prompt
        assert "사전 분석" in captured_prompt["supervisor_context"]

    @pytest.mark.asyncio
    async def test_reading_agent_includes_level_instructions(
        self, reading_state: TutorState
    ) -> None:
        """
        GIVEN a state with specific level
        WHEN reading_node is called
        THEN it should include level-specific instructions in the prompt
        """
        from tutor.agents.reading import reading_node

        reading_state["level"] = 1

        mock_response = MagicMock()
        mock_response.content = "Reading content"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("tutor.agents.reading.get_llm", return_value=mock_llm), patch(
            "tutor.agents.reading.get_level_instructions", return_value="Beginner level instructions"
        ) as mock_level:
            await reading_node(reading_state)

            mock_level.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_reading_agent_handles_error(self, reading_state: TutorState) -> None:
        """
        GIVEN a reading agent that encounters an error
        WHEN reading_node is called
        THEN it should return None for reading_result
        """
        from tutor.agents.reading import reading_node

        with patch("tutor.agents.reading.get_llm", side_effect=Exception("API Error")):
            result = await reading_node(reading_state)

        assert "reading_result" in result
        assert result["reading_result"] is None


class TestGrammarAgent:
    """Test cases for the grammar analysis agent (SPEC-UPDATE-001)."""

    @pytest.fixture
    def grammar_state(self) -> TutorState:
        """Create a TutorState for grammar agent testing."""
        return {
            "messages": [],
            "level": 3,
            "session_id": "test-session-123",
            "input_text": "She was walking to the store when she saw him.",
            "task_type": "analyze",
        }

    @pytest.mark.asyncio
    async def test_grammar_agent_returns_grammar_result(
        self, grammar_state: TutorState
    ) -> None:
        """
        GIVEN a state with input_text
        WHEN grammar_node is called
        THEN it should return a GrammarResult with Korean Markdown content
        """
        from tutor.agents.grammar import grammar_node

        mock_response = MagicMock()
        mock_response.content = "## 문법 포인트\n\n과거 진행형 (Past Continuous)..."

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("tutor.agents.grammar.get_llm", return_value=mock_llm), \
             patch("tutor.agents.grammar.render_prompt", return_value="Test prompt"):
            result = await grammar_node(grammar_state)

        assert "grammar_result" in result
        grammar_result = result["grammar_result"]
        assert isinstance(grammar_result, GrammarResult)
        assert "문법 포인트" in grammar_result.content

    @pytest.mark.asyncio
    async def test_grammar_agent_uses_config_model(self, grammar_state: TutorState) -> None:
        """
        GIVEN a grammar analysis request
        WHEN grammar_node is called
        THEN it should use GRAMMAR_MODEL from config (R1, R2)
        """
        from tutor.agents.grammar import grammar_node

        mock_response = MagicMock()
        mock_response.content = "Grammar content"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        mock_settings_obj = MagicMock()
        mock_settings_obj.GRAMMAR_MODEL = "gpt-4o-mini"

        with patch("tutor.agents.grammar.get_llm", return_value=mock_llm) as mock_get_llm, \
             patch("tutor.agents.grammar.get_settings", return_value=mock_settings_obj):
            await grammar_node(grammar_state)

            mock_get_llm.assert_called_once_with(mock_settings_obj.GRAMMAR_MODEL)

    @pytest.mark.asyncio
    async def test_grammar_agent_uses_raw_llm_invocation(
        self, grammar_state: TutorState
    ) -> None:
        """
        GIVEN a grammar analysis request
        WHEN grammar_node is called
        THEN it should use raw llm.ainvoke() (not with_structured_output)
        """
        from tutor.agents.grammar import grammar_node

        mock_response = MagicMock()
        mock_response.content = "Grammar content"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("tutor.agents.grammar.get_llm", return_value=mock_llm), \
             patch("tutor.agents.grammar.render_prompt", return_value="Test prompt"):
            await grammar_node(grammar_state)

        mock_llm.ainvoke.assert_called_once()
        mock_llm.with_structured_output.assert_not_called()

    @pytest.mark.asyncio
    async def test_grammar_agent_handles_malformed_response(
        self, grammar_state: TutorState
    ) -> None:
        """
        GIVEN a state with input_text
        WHEN grammar_node encounters an error
        THEN it should handle the error gracefully and return None
        """
        from tutor.agents.grammar import grammar_node

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("LLM API error")

        with patch("tutor.agents.grammar.get_llm", return_value=mock_llm):
            result = await grammar_node(grammar_state)

        assert "grammar_result" in result
        assert result["grammar_result"] is None


class TestVocabularyAgent:
    """Test cases for the vocabulary extraction agent (SPEC-UPDATE-001)."""

    @pytest.fixture
    def vocabulary_state(self) -> TutorState:
        """Create a TutorState for vocabulary agent testing."""
        return {
            "messages": [],
            "level": 3,
            "session_id": "test-session-123",
            "input_text": "The ephemeral beauty of sunset captivated everyone.",
            "task_type": "analyze",
        }

    @pytest.mark.asyncio
    async def test_vocabulary_agent_returns_vocabulary_result(
        self, vocabulary_state: TutorState
    ) -> None:
        """
        GIVEN a state with input_text
        WHEN vocabulary_node is called
        THEN it should return a VocabularyResult with VocabularyWordEntry objects
        """
        from tutor.agents.vocabulary import vocabulary_node

        # Mock Markdown output with ## headers
        mock_response = MagicMock()
        mock_response.content = (
            "## ephemeral\n\n"
            "### 1. 기본 뜻\n짧은 시간 동안만 지속되는\n\n"
            "### 2. 문장 속 의미\n이 문장에서는 찰나의 아름다움을 의미\n\n"
            "---\n\n"
            "## captivate\n\n"
            "### 1. 기본 뜻\n마음을 사로잡다\n\n"
            "### 2. 문장 속 의미\n황홀하게 만들다\n\n"
            "---"
        )

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("tutor.agents.vocabulary.get_llm", return_value=mock_llm), \
             patch("tutor.agents.vocabulary.render_prompt", return_value="Test prompt"):
            result = await vocabulary_node(vocabulary_state)

        assert "vocabulary_result" in result
        vocab_result = result["vocabulary_result"]
        assert isinstance(vocab_result, VocabularyResult)
        assert len(vocab_result.words) >= 1
        word = vocab_result.words[0]
        assert isinstance(word, VocabularyWordEntry)
        assert word.word == "ephemeral"
        assert "기본 뜻" in word.content

    @pytest.mark.asyncio
    async def test_vocabulary_agent_uses_config_model(
        self, vocabulary_state: TutorState
    ) -> None:
        """
        GIVEN a vocabulary extraction request
        WHEN vocabulary_node is called
        THEN it should use VOCABULARY_MODEL from config with max_tokens=6144 (R1, R2, R7)
        """
        from tutor.agents.vocabulary import vocabulary_node

        mock_response = MagicMock()
        mock_response.content = "## test\n\ncontent\n\n---"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        mock_settings_obj = MagicMock()
        mock_settings_obj.VOCABULARY_MODEL = "gpt-4o-mini"

        with patch("tutor.agents.vocabulary.get_llm", return_value=mock_llm) as mock_get_llm, \
             patch("tutor.agents.vocabulary.get_settings", return_value=mock_settings_obj):
            await vocabulary_node(vocabulary_state)

            mock_get_llm.assert_called_once_with(
                mock_settings_obj.VOCABULARY_MODEL, max_tokens=6144
            )

    @pytest.mark.asyncio
    async def test_vocabulary_agent_returns_empty_list_on_error(
        self, vocabulary_state: TutorState
    ) -> None:
        """
        GIVEN a vocabulary agent that encounters an error
        WHEN vocabulary_node is called
        THEN it should return empty VocabularyResult
        """
        from tutor.agents.vocabulary import vocabulary_node

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("API Error")

        with patch("tutor.agents.vocabulary.get_llm", return_value=mock_llm):
            result = await vocabulary_node(vocabulary_state)

        assert "vocabulary_result" in result
        vocab_result = result["vocabulary_result"]
        assert isinstance(vocab_result, VocabularyResult)
        assert len(vocab_result.words) == 0

    @pytest.mark.asyncio
    async def test_vocabulary_agent_returns_empty_list_for_simple_text(
        self, vocabulary_state: TutorState
    ) -> None:
        """
        GIVEN a state with simple input_text
        WHEN vocabulary_node returns empty Markdown (no ## headers)
        THEN it should return empty vocabulary list
        """
        from tutor.agents.vocabulary import vocabulary_node

        vocabulary_state["input_text"] = "The cat sat on the mat."

        mock_response = MagicMock()
        mock_response.content = "단어 설명이 필요한 어휘가 없습니다."

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("tutor.agents.vocabulary.get_llm", return_value=mock_llm), \
             patch("tutor.agents.vocabulary.render_prompt", return_value="Test prompt"):
            result = await vocabulary_node(vocabulary_state)

        assert "vocabulary_result" in result
        vocab_result = result["vocabulary_result"]
        assert isinstance(vocab_result, VocabularyResult)
        assert len(vocab_result.words) == 0


class TestImageProcessorAgent:
    """Test cases for the image processor agent."""

    @pytest.fixture
    def image_state(self) -> TutorState:
        """Create a TutorState for image processing testing."""
        return {
            "messages": [],
            "level": 3,
            "session_id": "test-session-123",
            "input_text": "",  # No text input for image processing
            "task_type": "image_process",
        }

    @pytest.mark.asyncio
    async def test_image_processor_extracts_text(self, image_state: TutorState) -> None:
        """
        GIVEN a state with image_data
        WHEN image_processor_node is called
        THEN it should extract text from the image
        """
        from tutor.agents.image_processor import image_processor_node

        # Create proper base64 encoded test data
        test_text = "The quick brown fox jumps over the lazy dog."
        test_bytes = test_text.encode("utf-8")
        base64_data = base64.b64encode(test_bytes).decode("utf-8")

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = "The quick brown fox jumps over the lazy dog."
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        # Add image_data to state
        image_state["image_data"] = base64_data  # Properly base64 encoded
        image_state["mime_type"] = "image/jpeg"

        with patch("tutor.agents.image_processor.get_llm", return_value=mock_llm):
            result = await image_processor_node(image_state)

        assert "extracted_text" in result
        assert result["extracted_text"] == "The quick brown fox jumps over the lazy dog."

    @pytest.mark.asyncio
    async def test_image_processor_handles_no_text_found(
        self, image_state: TutorState
    ) -> None:
        """
        GIVEN a state with image_data containing no text
        WHEN image_processor_node is called
        THEN it should return empty string for extracted_text
        """
        from tutor.agents.image_processor import image_processor_node

        # Create proper base64 encoded test data
        test_bytes = b"test data"
        base64_data = base64.b64encode(test_bytes).decode("utf-8")

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = "No text found in image."
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        # Add image_data to state
        image_state["image_data"] = base64_data
        image_state["mime_type"] = "image/jpeg"

        with patch("tutor.agents.image_processor.get_llm", return_value=mock_llm):
            result = await image_processor_node(image_state)

        assert "extracted_text" in result
        # Empty or no-text indicator
        assert result["extracted_text"] == "" or "No text found" in result["extracted_text"]


class TestAggregatorAgent:
    """Test cases for the result aggregation agent."""

    @pytest.fixture
    def full_state(self) -> TutorState:
        """Create a TutorState with all results for aggregation (SPEC-UPDATE-001 schemas)."""
        return {
            "messages": [],
            "level": 3,
            "session_id": "test-session-123",
            "input_text": "Test text for analysis.",
            "task_type": "analyze",
            "reading_result": ReadingResult(
                content="Korean Markdown reading content with slash reading",
            ),
            "grammar_result": GrammarResult(
                content="Korean Markdown grammar explanation content",
            ),
            "vocabulary_result": VocabularyResult(
                words=[
                    VocabularyWordEntry(
                        word="analysis",
                        content="Korean etymology explanation for analysis",
                    )
                ]
            ),
        }

    def test_aggregator_combines_results(self, full_state: TutorState) -> None:
        """
        GIVEN a state with all three tutor agent results
        WHEN aggregator_node is called
        THEN it should return an AnalyzeResponse with all results
        """
        from tutor.agents.aggregator import aggregator_node

        result = aggregator_node(full_state)

        assert "analyze_response" in result
        response = result["analyze_response"]
        assert isinstance(response, AnalyzeResponse)
        assert response.session_id == "test-session-123"
        assert response.reading is not None
        assert response.grammar is not None
        assert response.vocabulary is not None
        assert "slash reading" in response.reading.content
        assert "grammar explanation" in response.grammar.content
        assert len(response.vocabulary.words) == 1

    def test_aggregator_handles_partial_results(self) -> None:
        """
        GIVEN a state with only some tutor agent results
        WHEN aggregator_node is called
        THEN it should return AnalyzeResponse with available results only
        """
        from tutor.agents.aggregator import aggregator_node

        partial_state: TutorState = {
            "messages": [],
            "level": 3,
            "session_id": "partial-session-456",
            "input_text": "Partial test.",
            "task_type": "analyze",
            "reading_result": ReadingResult(
                content="Partial reading content",
            ),
            # Missing grammar and vocabulary results
        }

        result = aggregator_node(partial_state)

        assert "analyze_response" in result
        response = result["analyze_response"]
        assert isinstance(response, AnalyzeResponse)
        assert response.session_id == "partial-session-456"
        assert response.reading is not None
        assert response.grammar is None
        assert response.vocabulary is None

    def test_aggregator_handles_all_errors(self) -> None:
        """
        GIVEN a state with no tutor agent results (all failed)
        WHEN aggregator_node is called
        THEN it should return AnalyzeResponse with all None fields
        """
        from tutor.agents.aggregator import aggregator_node

        error_state: TutorState = {
            "messages": [],
            "level": 3,
            "session_id": "error-session-789",
            "input_text": "Error test.",
            "task_type": "analyze",
            # No results - all agents failed
        }

        result = aggregator_node(error_state)

        assert "analyze_response" in result
        response = result["analyze_response"]
        assert isinstance(response, AnalyzeResponse)
        assert response.session_id == "error-session-789"
        assert response.reading is None
        assert response.grammar is None
        assert response.vocabulary is None


class TestAgentErrorHandling:
    """Test cases for agent error handling."""

    @pytest.mark.asyncio
    async def test_agent_handles_error_gracefully(self) -> None:
        """
        GIVEN an agent that encounters an error
        WHEN the agent is called
        THEN it should return None for its result field
        """
        from tutor.agents.reading import reading_node

        error_state: TutorState = {
            "messages": [],
            "level": 3,
            "session_id": "error-test",
            "input_text": "Test",
            "task_type": "analyze",
        }

        # Mock get_llm to raise an exception
        with patch("tutor.agents.reading.get_llm", side_effect=Exception("API Error")):
            result = await reading_node(error_state)

        # Should handle error gracefully
        assert "reading_result" in result
        assert result["reading_result"] is None
