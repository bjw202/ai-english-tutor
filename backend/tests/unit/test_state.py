"""
Unit tests for TutorState TypedDict.

Tests follow the Arrange-Act-Assert pattern and validate:
- TutorState is a valid TypedDict
- Required fields are present
- Optional fields can be None
- Valid TutorState instances can be created
"""

from __future__ import annotations

import uuid

from tutor.schemas import GrammarResult, ReadingResult, SentenceEntry, SupervisorAnalysis, VocabularyResult, VocabularyWordEntry


class TestTutorStateTypedDict:
    """Test suite for TutorState TypedDict definition."""

    def test_tutor_state_is_typed_dict(self):
        """Test that TutorState is a valid TypedDict."""
        # Arrange & Act
        from tutor.state import TutorState

        # Assert
        assert isinstance(TutorState, type)
        # TypedDict is a special form, check if it has TypedDict-specific attributes
        assert hasattr(TutorState, "__annotations__")

    def test_tutor_state_has_required_fields(self):
        """Test that TutorState has all required fields."""
        # Arrange & Act
        from tutor.state import TutorState

        # Assert - check all required fields are present
        annotations = TutorState.__annotations__
        required_fields = ["messages", "level", "session_id", "input_text", "task_type"]

        for field in required_fields:
            assert field in annotations, f"Required field '{field}' not found in TutorState"

    def test_tutor_state_has_optional_fields(self):
        """Test that TutorState has all optional fields."""
        # Arrange & Act
        from tutor.state import TutorState

        # Assert - check all optional fields are present
        annotations = TutorState.__annotations__
        optional_fields = [
            "reading_result",
            "grammar_result",
            "vocabulary_result",
            "extracted_text",
            "supervisor_analysis",
        ]

        for field in optional_fields:
            assert field in annotations, f"Optional field '{field}' not found in TutorState"

    def test_tutor_state_has_supervisor_analysis_field(self):
        """Test that TutorState has supervisor_analysis optional field (SPEC-UPDATE-001)."""
        from tutor.state import TutorState

        annotations = TutorState.__annotations__
        assert "supervisor_analysis" in annotations, \
            "supervisor_analysis field not found in TutorState"

    def test_tutor_state_field_types(self):
        """Test that TutorState fields have correct type annotations."""
        # Arrange & Act
        from tutor.state import TutorState

        # Assert
        annotations = TutorState.__annotations__

        # Check messages is list[dict]
        assert "messages" in annotations
        # Note: TypedDict uses __origin__ and __args__ for generic types

        # Check level is int
        assert "level" in annotations

        # Check session_id is str
        assert "session_id" in annotations

        # Check input_text is str
        assert "input_text" in annotations

        # Check task_type is str
        assert "task_type" in annotations

    def test_create_valid_tutor_state_with_minimal_fields(self):
        """Test creating a valid TutorState with only required fields."""
        # Arrange
        from tutor.state import TutorState

        session_id = str(uuid.uuid4())

        # Act
        state: TutorState = {
            "messages": [],
            "level": 3,
            "session_id": session_id,
            "input_text": "Hello, world!",
            "task_type": "analyze",
        }

        # Assert
        assert isinstance(state, dict)
        assert state["messages"] == []
        assert state["level"] == 3
        assert state["session_id"] == session_id
        assert state["input_text"] == "Hello, world!"
        assert state["task_type"] == "analyze"

    def test_create_valid_tutor_state_with_all_fields(self):
        """Test creating a valid TutorState with all fields (SPEC-UPDATE-001 schemas)."""
        # Arrange
        from tutor.state import TutorState

        session_id = str(uuid.uuid4())

        reading_result = ReadingResult(
            content="Korean Markdown reading content",
        )

        grammar_result = GrammarResult(
            content="Korean Markdown grammar content",
        )

        vocabulary_result = VocabularyResult(
            words=[
                VocabularyWordEntry(
                    word="test",
                    content="Korean etymology content for test",
                )
            ]
        )

        supervisor_analysis = SupervisorAnalysis(
            sentences=[SentenceEntry(text="Test sentence.", difficulty=3, focus=["reading"])],
            overall_difficulty=3,
            focus_summary=["reading", "grammar"],
        )

        # Act
        state: TutorState = {
            "messages": [{"role": "user", "content": "Hello"}],
            "level": 5,
            "session_id": session_id,
            "input_text": "This is a test text.",
            "task_type": "analyze",
            "reading_result": reading_result,
            "grammar_result": grammar_result,
            "vocabulary_result": vocabulary_result,
            "extracted_text": "OCR extracted text",
            "supervisor_analysis": supervisor_analysis,
        }

        # Assert
        assert state["messages"] == [{"role": "user", "content": "Hello"}]
        assert state["level"] == 5
        assert state["session_id"] == session_id
        assert state["input_text"] == "This is a test text."
        assert state["task_type"] == "analyze"
        assert state["reading_result"] == reading_result
        assert state["grammar_result"] == grammar_result
        assert state["vocabulary_result"] == vocabulary_result
        assert state["extracted_text"] == "OCR extracted text"
        assert state["supervisor_analysis"] == supervisor_analysis

    def test_tutor_state_supervisor_analysis_can_be_none(self):
        """Test that supervisor_analysis field in TutorState can be None."""
        from tutor.state import TutorState

        session_id = str(uuid.uuid4())

        state: TutorState = {
            "messages": [],
            "level": 2,
            "session_id": session_id,
            "input_text": "Test",
            "task_type": "analyze",
            "supervisor_analysis": None,
        }

        assert state["supervisor_analysis"] is None

    def test_tutor_state_optional_fields_can_be_none(self):
        """Test that optional fields in TutorState can be None."""
        # Arrange
        from tutor.state import TutorState

        session_id = str(uuid.uuid4())

        # Act - Create state with optional fields as None
        state: TutorState = {
            "messages": [],
            "level": 2,
            "session_id": session_id,
            "input_text": "Test",
            "task_type": "chat",
            "reading_result": None,
            "grammar_result": None,
            "vocabulary_result": None,
            "extracted_text": None,
            "supervisor_analysis": None,
        }

        # Assert
        assert state["reading_result"] is None
        assert state["grammar_result"] is None
        assert state["vocabulary_result"] is None
        assert state["extracted_text"] is None
        assert state["supervisor_analysis"] is None

    def test_tutor_state_task_type_values(self):
        """Test that TutorState accepts valid task_type values."""
        # Arrange
        from tutor.state import TutorState

        session_id = str(uuid.uuid4())

        # Act & Assert - Test all valid task types
        valid_task_types = ["analyze", "image_process", "chat"]

        for task_type in valid_task_types:
            state: TutorState = {
                "messages": [],
                "level": 3,
                "session_id": session_id,
                "input_text": "Test",
                "task_type": task_type,
            }
            assert state["task_type"] == task_type

    def test_tutor_state_level_range(self):
        """Test that TutorState accepts valid level values (1-5)."""
        # Arrange
        from tutor.state import TutorState

        session_id = str(uuid.uuid4())

        # Act & Assert - Test all valid levels
        for level in range(1, 6):
            state: TutorState = {
                "messages": [],
                "level": level,
                "session_id": session_id,
                "input_text": "Test",
                "task_type": "analyze",
            }
            assert state["level"] == level

    def test_tutor_state_messages_is_list_of_dict(self):
        """Test that messages field accepts list of dict."""
        # Arrange
        from tutor.state import TutorState

        session_id = str(uuid.uuid4())

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Act
        state: TutorState = {
            "messages": messages,
            "level": 3,
            "session_id": session_id,
            "input_text": "Test",
            "task_type": "chat",
        }

        # Assert
        assert state["messages"] == messages
        assert len(state["messages"]) == 2
        assert state["messages"][0]["role"] == "user"

    def test_tutor_state_session_id_is_string(self):
        """Test that session_id field accepts string values."""
        # Arrange
        from tutor.state import TutorState

        # Act & Assert - Test with different string formats
        session_ids = [
            str(uuid.uuid4()),
            "session-123",
            "user_session_abc",
        ]

        for session_id in session_ids:
            state: TutorState = {
                "messages": [],
                "level": 3,
                "session_id": session_id,
                "input_text": "Test",
                "task_type": "analyze",
            }
            assert state["session_id"] == session_id
            assert isinstance(state["session_id"], str)
