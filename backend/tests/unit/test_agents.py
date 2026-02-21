"""
Unit tests for AI English Tutor agents.

Tests all agent nodes for the LangGraph workflow including:
- Supervisor: Routes based on task_type
- Reading: Reading comprehension analysis (Claude Sonnet)
- Grammar: Grammar analysis (GPT-4o)
- Vocabulary: Vocabulary extraction (Claude Haiku)
- ImageProcessor: Text extraction from images
- Aggregator: Combines all tutor agent results

All tests use mocked LLM responses to avoid actual API calls.
"""

from __future__ import annotations

import base64

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tutor.schemas import (
    AnalyzeResponse,
    GrammarResult,
    ReadingResult,
    VocabularyResult,
    VocabularyWord,
)
from tutor.state import TutorState


class TestSupervisorAgent:
    """Test cases for the supervisor routing agent."""

    @pytest.fixture
    def base_state(self) -> TutorState:
        """Create a base TutorState for testing."""
        return {
            "messages": [],
            "level": 3,
            "session_id": "test-session-123",
            "input_text": "Hello, world!",
            "task_type": "analyze",
        }

    def test_supervisor_routes_to_analyze(self, base_state: TutorState) -> None:
        """
        GIVEN a state with task_type='analyze'
        WHEN supervisor_node is called
        THEN it should route to parallel execution of reading, grammar, and vocabulary agents
        """
        from tutor.agents.supervisor import supervisor_node

        base_state["task_type"] = "analyze"
        result = supervisor_node(base_state)

        assert "next_nodes" in result
        assert set(result["next_nodes"]) == {"reading", "grammar", "vocabulary"}

    def test_supervisor_routes_to_image_process(self, base_state: TutorState) -> None:
        """
        GIVEN a state with task_type='image_process'
        WHEN supervisor_node is called
        THEN it should route to image_processor first
        """
        from tutor.agents.supervisor import supervisor_node

        base_state["task_type"] = "image_process"
        result = supervisor_node(base_state)

        assert "next_nodes" in result
        assert result["next_nodes"] == ["image_processor"]

    def test_supervisor_routes_to_chat(self, base_state: TutorState) -> None:
        """
        GIVEN a state with task_type='chat'
        WHEN supervisor_node is called
        THEN it should route to chat handler
        """
        from tutor.agents.supervisor import supervisor_node

        base_state["task_type"] = "chat"
        result = supervisor_node(base_state)

        assert "next_nodes" in result
        assert result["next_nodes"] == ["chat"]

    def test_supervisor_handles_unknown_task_type(self, base_state: TutorState) -> None:
        """
        GIVEN a state with unknown task_type
        WHEN supervisor_node is called
        THEN it should return empty node list
        """
        from tutor.agents.supervisor import supervisor_node

        base_state["task_type"] = "unknown"
        result = supervisor_node(base_state)

        assert "next_nodes" in result
        assert result["next_nodes"] == []

    def test_supervisor_default_to_analyze(self, base_state: TutorState) -> None:
        """
        GIVEN a state without task_type
        WHEN supervisor_node is called with default
        THEN it should default to analyze routing
        """
        from tutor.agents.supervisor import supervisor_node

        # Remove task_type to test default behavior
        del base_state["task_type"]
        result = supervisor_node(base_state)

        assert "next_nodes" in result
        assert set(result["next_nodes"]) == {"reading", "grammar", "vocabulary"}


class TestReadingAgent:
    """Test cases for the reading comprehension agent."""

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
        THEN it should return a ReadingResult with summary, main_topic, and emotional_tone
        """
        from tutor.agents.reading import reading_node

        # Create the expected result object
        expected_result = ReadingResult(
            summary="A fox jumps over a dog.",
            main_topic="Animal behavior",
            emotional_tone="Playful"
        )

        # Mock structured LLM that returns the result directly
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = expected_result

        # Mock base LLM with with_structured_output method
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("tutor.agents.reading.get_llm", return_value=mock_llm), \
             patch("tutor.agents.reading.render_prompt", return_value="Test prompt"):
            result = await reading_node(reading_state)

        assert "reading_result" in result
        reading_result = result["reading_result"]
        assert isinstance(reading_result, ReadingResult)
        assert reading_result.summary == "A fox jumps over a dog."
        assert reading_result.main_topic == "Animal behavior"
        assert reading_result.emotional_tone == "Playful"

    @pytest.mark.asyncio
    async def test_reading_agent_uses_claude_sonnet(
        self, reading_state: TutorState
    ) -> None:
        """
        GIVEN a reading analysis request
        WHEN reading_node is called
        THEN it should use Claude Sonnet model
        """
        from tutor.agents.reading import reading_node

        # Create the expected result
        expected_result = ReadingResult(
            summary="Test",
            main_topic="Test",
            emotional_tone="Neutral"
        )

        # Mock structured LLM
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = expected_result

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("tutor.agents.reading.get_llm", return_value=mock_llm) as mock_get_llm:
            await reading_node(reading_state)

            mock_get_llm.assert_called_once_with("claude-sonnet-4-5")

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

        # Create the expected result
        expected_result = ReadingResult(
            summary="Test",
            main_topic="Test",
            emotional_tone="Neutral"
        )

        # Mock structured LLM
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = expected_result

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("tutor.agents.reading.get_llm", return_value=mock_llm), patch(
            "tutor.agents.reading.get_level_instructions", return_value="Beginner level instructions"
        ) as mock_level:
            await reading_node(reading_state)

            mock_level.assert_called_once_with(1)


class TestGrammarAgent:
    """Test cases for the grammar analysis agent."""

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
        THEN it should return a GrammarResult with tenses, voice, sentence_structure, and analysis
        """
        from tutor.agents.grammar import grammar_node

        # Create the expected result
        expected_result = GrammarResult(
            tenses=["past continuous", "simple past"],
            voice="active",
            sentence_structure="complex",
            analysis="The sentence uses past continuous for background action and simple past for interrupting action."
        )

        # Mock structured LLM
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = expected_result

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("tutor.agents.grammar.get_llm", return_value=mock_llm), \
             patch("tutor.agents.grammar.render_prompt", return_value="Test prompt"):
            result = await grammar_node(grammar_state)

        assert "grammar_result" in result
        grammar_result = result["grammar_result"]
        assert isinstance(grammar_result, GrammarResult)
        assert "past continuous" in grammar_result.tenses
        assert "simple past" in grammar_result.tenses
        assert grammar_result.voice == "active"
        assert grammar_result.sentence_structure == "complex"
        assert "background action" in grammar_result.analysis

    @pytest.mark.asyncio
    async def test_grammar_agent_uses_gpt_4o(self, grammar_state: TutorState) -> None:
        """
        GIVEN a grammar analysis request
        WHEN grammar_node is called
        THEN it should use GPT-4o model
        """
        from tutor.agents.grammar import grammar_node

        # Create the expected result
        expected_result = GrammarResult(
            tenses=[],
            voice="active",
            sentence_structure="simple",
            analysis="Test"
        )

        # Mock structured LLM
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = expected_result

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("tutor.agents.grammar.get_llm", return_value=mock_llm) as mock_get_llm:
            await grammar_node(grammar_state)

            mock_get_llm.assert_called_once_with("gpt-4o")

    @pytest.mark.asyncio
    async def test_grammar_agent_handles_malformed_response(
        self, grammar_state: TutorState
    ) -> None:
        """
        GIVEN a state with input_text
        WHEN grammar_node receives malformed JSON response
        THEN it should handle the error gracefully
        """
        from tutor.agents.grammar import grammar_node

        # Mock structured LLM that raises an exception
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.side_effect = Exception("Invalid JSON response")

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("tutor.agents.grammar.get_llm", return_value=mock_llm):
            result = await grammar_node(grammar_state)

        # Should return error indicator
        assert "grammar_result" in result
        assert result["grammar_result"] is None


class TestVocabularyAgent:
    """Test cases for the vocabulary extraction agent."""

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
        THEN it should return a VocabularyResult with list of vocabulary words
        """
        from tutor.agents.vocabulary import vocabulary_node

        # Create the expected result
        expected_result = VocabularyResult(
            words=[
                VocabularyWord(
                    term="ephemeral",
                    meaning="Lasting for a very short time",
                    usage="The ephemeral beauty of cherry blossoms.",
                    synonyms=["fleeting", "transient", "momentary"]
                )
            ]
        )

        # Mock structured LLM
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = expected_result

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("tutor.agents.vocabulary.get_llm", return_value=mock_llm), \
             patch("tutor.agents.vocabulary.render_prompt", return_value="Test prompt"):
            result = await vocabulary_node(vocabulary_state)

        assert "vocabulary_result" in result
        vocab_result = result["vocabulary_result"]
        assert isinstance(vocab_result, VocabularyResult)
        assert len(vocab_result.words) == 1
        word = vocab_result.words[0]
        assert isinstance(word, VocabularyWord)
        assert word.term == "ephemeral"
        assert word.meaning == "Lasting for a very short time"
        assert "cherry blossoms" in word.usage
        assert "fleeting" in word.synonyms

    @pytest.mark.asyncio
    async def test_vocabulary_agent_uses_claude_haiku(
        self, vocabulary_state: TutorState
    ) -> None:
        """
        GIVEN a vocabulary extraction request
        WHEN vocabulary_node is called
        THEN it should use Claude Haiku model
        """
        from tutor.agents.vocabulary import vocabulary_node

        # Create the expected result
        expected_result = VocabularyResult(words=[])

        # Mock structured LLM
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = expected_result

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("tutor.agents.vocabulary.get_llm", return_value=mock_llm) as mock_get_llm:
            await vocabulary_node(vocabulary_state)

            mock_get_llm.assert_called_once_with("claude-haiku-4-5")

    @pytest.mark.asyncio
    async def test_vocabulary_agent_returns_empty_list_for_simple_text(
        self, vocabulary_state: TutorState
    ) -> None:
        """
        GIVEN a state with simple input_text
        WHEN vocabulary_node is called
        THEN it should return empty vocabulary list for basic words
        """
        from tutor.agents.vocabulary import vocabulary_node

        vocabulary_state["input_text"] = "The cat sat on the mat."

        # Create the expected result with empty words list
        expected_result = VocabularyResult(words=[])

        # Mock structured LLM
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = expected_result

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

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
        """Create a TutorState with all results for aggregation."""
        return {
            "messages": [],
            "level": 3,
            "session_id": "test-session-123",
            "input_text": "Test text for analysis.",
            "task_type": "analyze",
            "reading_result": ReadingResult(
                summary="Test summary",
                main_topic="Testing",
                emotional_tone="Neutral",
            ),
            "grammar_result": GrammarResult(
                tenses=["present simple"],
                voice="active",
                sentence_structure="simple",
                analysis="Simple present tense statement.",
            ),
            "vocabulary_result": VocabularyResult(
                words=[
                    VocabularyWord(
                        term="analysis",
                        meaning="Examination of something",
                        usage="The analysis was complete.",
                        synonyms=["examination", "evaluation", "study"],
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
        assert response.reading.summary == "Test summary"
        assert response.grammar.voice == "active"
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
                summary="Partial summary",
                main_topic="Partial",
                emotional_tone="Neutral",
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
