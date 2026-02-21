"""Unit tests for service layer components.

Tests for:
- SessionManager: In-memory session management with TTL
- SSE formatting: Server-Sent Events formatting utilities
- Image validation and preprocessing: Image handling utilities
"""

import base64
import json
from datetime import datetime, timedelta

import pytest

from tutor.config import Settings
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


class TestSessionManager:
    """Test suite for SessionManager class."""

    def test_session_create_and_retrieve(self):
        """Test that a created session can be retrieved with all its data."""
        # Arrange: Create a session manager instance
        manager = SessionManager(ttl_hours=24)

        # Act: Create a new session
        session_id = manager.create()

        # Assert: Verify session was created correctly
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID4 format

        # Assert: Verify session can be retrieved
        session = manager.get(session_id)
        assert session is not None
        assert session["id"] == session_id
        assert session["messages"] == []
        assert "created_at" in session
        assert "expires_at" in session

    def test_session_add_message(self):
        """Test that messages can be added to a session history."""
        # Arrange: Create a session
        manager = SessionManager(ttl_hours=24)
        session_id = manager.create()

        # Act: Add messages to the session
        result1 = manager.add_message(session_id, "user", "Hello, how are you?")
        result2 = manager.add_message(session_id, "assistant", "I'm doing well, thank you!")

        # Assert: Verify messages were added
        assert result1 is True
        assert result2 is True

        session = manager.get(session_id)
        assert len(session["messages"]) == 2
        assert session["messages"][0] == {"role": "user", "content": "Hello, how are you?"}
        assert session["messages"][1] == {"role": "assistant", "content": "I'm doing well, thank you!"}

    def test_session_ttl_expiry(self):
        """Test that expired sessions are not returned."""
        # Arrange: Create a session manager with very short TTL
        manager = SessionManager(ttl_hours=0)  # Expired immediately
        session_id = manager.create()

        # Act: Try to retrieve the expired session
        session = manager.get(session_id)

        # Assert: Session should not be found (expired)
        assert session is None

    def test_session_not_found(self):
        """Test that getting a non-existent session returns None."""
        # Arrange: Create a session manager
        manager = SessionManager(ttl_hours=24)

        # Act: Try to get a non-existent session
        session = manager.get("non-existent-session-id")

        # Assert: Should return None
        assert session is None

    def test_session_delete(self):
        """Test that a session can be deleted."""
        # Arrange: Create a session
        manager = SessionManager(ttl_hours=24)
        session_id = manager.create()

        # Act: Delete the session
        result = manager.delete(session_id)

        # Assert: Verify deletion was successful
        assert result is True

        # Assert: Verify session no longer exists
        session = manager.get(session_id)
        assert session is None

    def test_session_delete_non_existent(self):
        """Test that deleting a non-existent session returns False."""
        # Arrange: Create a session manager
        manager = SessionManager(ttl_hours=24)

        # Act: Try to delete a non-existent session
        result = manager.delete("non-existent-session-id")

        # Assert: Should return False
        assert result is False

    def test_session_add_message_non_existent(self):
        """Test that adding a message to a non-existent session returns False."""
        # Arrange: Create a session manager
        manager = SessionManager(ttl_hours=24)

        # Act: Try to add a message to a non-existent session
        result = manager.add_message("non-existent-session-id", "user", "Hello")

        # Assert: Should return False
        assert result is False

    def test_global_session_manager_instance(self):
        """Test that the global session_manager instance uses settings."""
        # Arrange: Get settings instance
        settings = Settings()

        # Assert: Verify global instance exists
        # Note: session_manager is a proxy, so we check it behaves like SessionManager
        assert session_manager is not None
        # Test by calling a method to verify it's a working proxy
        session_id = session_manager.create()
        assert session_id is not None
        # Clean up
        session_manager.delete(session_id)


class TestSSEFormatting:
    """Test suite for Server-Sent Events formatting functions."""

    def test_sse_format_reading_chunk(self):
        """Test that reading chunks are formatted correctly as SSE events."""
        # Arrange: Prepare test data
        data = {"summary": "Test summary", "main_topic": "Test topic"}

        # Act: Format as SSE reading chunk
        result = format_reading_chunk(data)

        # Assert: Verify SSE format
        assert result.startswith("event: reading_chunk\ndata: ")
        assert "\n\n" in result

        # Assert: Verify JSON data can be parsed
        lines = result.strip().split("\n")
        data_line = lines[1].replace("data: ", "")
        parsed = json.loads(data_line)
        assert parsed == data

    def test_sse_format_grammar_chunk(self):
        """Test that grammar chunks are formatted correctly as SSE events."""
        # Arrange: Prepare test data
        data = {"tenses": ["past"], "voice": "active"}

        # Act: Format as SSE grammar chunk
        result = format_grammar_chunk(data)

        # Assert: Verify SSE format
        assert result.startswith("event: grammar_chunk\ndata: ")
        assert "\n\n" in result

        # Assert: Verify JSON data can be parsed
        lines = result.strip().split("\n")
        data_line = lines[1].replace("data: ", "")
        parsed = json.loads(data_line)
        assert parsed == data

    def test_sse_format_vocabulary_chunk(self):
        """Test that vocabulary chunks are formatted correctly as SSE events."""
        # Arrange: Prepare test data
        data = {"words": [{"term": "test", "meaning": "examination"}]}

        # Act: Format as SSE vocabulary chunk
        result = format_vocabulary_chunk(data)

        # Assert: Verify SSE format
        assert result.startswith("event: vocabulary_chunk\ndata: ")
        assert "\n\n" in result

        # Assert: Verify JSON data can be parsed
        lines = result.strip().split("\n")
        data_line = lines[1].replace("data: ", "")
        parsed = json.loads(data_line)
        assert parsed == data

    def test_sse_format_done_event(self):
        """Test that done events are formatted correctly as SSE events."""
        # Arrange: Prepare test session ID
        session_id = "test-session-123"

        # Act: Format as SSE done event
        result = format_done_event(session_id)

        # Assert: Verify SSE format
        assert result.startswith("event: done\ndata: ")
        assert "\n\n" in result

        # Assert: Verify JSON data can be parsed
        lines = result.strip().split("\n")
        data_line = lines[1].replace("data: ", "")
        parsed = json.loads(data_line)
        assert parsed["session_id"] == session_id
        assert parsed["status"] == "complete"

    def test_sse_format_error_event(self):
        """Test that error events are formatted correctly as SSE events."""
        # Arrange: Prepare test error message
        message = "Something went wrong"
        code = "validation_error"

        # Act: Format as SSE error event
        result = format_error_event(message, code)

        # Assert: Verify SSE format
        assert result.startswith("event: error\ndata: ")
        assert "\n\n" in result

        # Assert: Verify JSON data can be parsed
        lines = result.strip().split("\n")
        data_line = lines[1].replace("data: ", "")
        parsed = json.loads(data_line)
        assert parsed["message"] == message
        assert parsed["code"] == code

    def test_sse_format_error_event_default_code(self):
        """Test that error events use default code when not provided."""
        # Arrange: Prepare test error message
        message = "Default error"

        # Act: Format as SSE error event without code
        result = format_error_event(message)

        # Assert: Verify default code is used
        lines = result.strip().split("\n")
        data_line = lines[1].replace("data: ", "")
        parsed = json.loads(data_line)
        assert parsed["message"] == message
        assert parsed["code"] == "error"

    def test_sse_format_base_event(self):
        """Test the base SSE event formatting function."""
        # Arrange: Prepare test event type and data
        event_type = "custom_event"
        data = {"key": "value", "number": 123}

        # Act: Format as SSE event
        result = format_sse_event(event_type, data)

        # Assert: Verify SSE format structure
        expected = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        assert result == expected


class TestImageValidation:
    """Test suite for image validation and preprocessing functions."""

    def test_image_validate_valid_image(self):
        """Test that a valid image passes validation."""
        # Arrange: Create a small valid base64 image
        image_data = base64.b64encode(b"fake_image_data").decode()
        mime_type = "image/jpeg"

        # Act: Validate the image
        is_valid, error_message = validate_image(image_data, mime_type)

        # Assert: Should pass validation
        assert is_valid is True
        assert error_message == ""

    def test_image_validate_unsupported_mime_type(self):
        """Test that unsupported MIME types fail validation."""
        # Arrange: Create image data with unsupported MIME type
        image_data = base64.b64encode(b"fake_image_data").decode()
        mime_type = "image/gif"

        # Act: Validate the image
        is_valid, error_message = validate_image(image_data, mime_type)

        # Assert: Should fail validation
        assert is_valid is False
        assert "Unsupported image format" in error_message
        assert "image/gif" in error_message

    def test_image_validate_size_limit(self):
        """Test that images exceeding size limit fail validation."""
        # Arrange: Create base64 data that decodes to > 10MB
        large_data = b"x" * (11 * 1024 * 1024)  # 11MB
        image_data = base64.b64encode(large_data).decode()
        mime_type = "image/jpeg"

        # Act: Validate the image
        is_valid, error_message = validate_image(image_data, mime_type)

        # Assert: Should fail validation
        assert is_valid is False
        assert "exceeds limit" in error_message
        assert "10MB" in error_message

    def test_image_validate_invalid_base64(self):
        """Test that invalid base64 data fails validation."""
        # Arrange: Create invalid base64 data
        invalid_base64 = "this_is_not_valid_base64!!!"
        mime_type = "image/jpeg"

        # Act: Validate the image
        is_valid, error_message = validate_image(invalid_base64, mime_type)

        # Assert: Should fail validation
        assert is_valid is False
        assert "Invalid base64 data" in error_message

    def test_image_validate_all_allowed_mime_types(self):
        """Test that all allowed MIME types pass validation."""
        # Arrange: Test all allowed MIME types
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        image_data = base64.b64encode(b"fake_image_data").decode()

        # Act & Assert: Each type should pass
        for mime_type in allowed_types:
            is_valid, error_message = validate_image(image_data, mime_type)
            assert is_valid is True, f"Failed for {mime_type}: {error_message}"
            assert error_message == ""


class TestImagePreprocessing:
    """Test suite for image preprocessing functions."""

    def test_image_preprocess_for_llm(self):
        """Test that images are preprocessed correctly for LLM consumption."""
        # Arrange: Prepare test data
        image_data = base64.b64encode(b"fake_image_data").decode()
        mime_type = "image/jpeg"

        # Act: Preprocess image for LLM
        result = preprocess_image_for_llm(image_data, mime_type)

        # Assert: Verify structure
        assert result["type"] == "image_url"
        assert "image_url" in result
        assert "url" in result["image_url"]

        # Assert: Verify data URI format
        expected_url = f"data:{mime_type};base64,{image_data}"
        assert result["image_url"]["url"] == expected_url

    def test_image_preprocess_different_mime_types(self):
        """Test preprocessing with different MIME types."""
        # Arrange: Prepare test data for different types
        test_cases = [
            ("image/jpeg", base64.b64encode(b"jpeg_data").decode()),
            ("image/png", base64.b64encode(b"png_data").decode()),
            ("image/webp", base64.b64encode(b"webp_data").decode()),
        ]

        # Act & Assert: Each type should produce correct format
        for mime_type, image_data in test_cases:
            result = preprocess_image_for_llm(image_data, mime_type)
            expected_url = f"data:{mime_type};base64,{image_data}"
            assert result["image_url"]["url"] == expected_url

    def test_image_preprocess_structure_matches_langchain_format(self):
        """Test that preprocessed image matches LangChain vision API format."""
        # Arrange: Prepare test data
        image_data = base64.b64encode(b"fake_image_data").decode()
        mime_type = "image/jpeg"

        # Act: Preprocess image
        result = preprocess_image_for_llm(image_data, mime_type)

        # Assert: Verify LangChain-compatible structure
        # LangChain expects: {"type": "image_url", "image_url": {"url": "data:..."}}
        assert isinstance(result, dict)
        assert set(result.keys()) == {"type", "image_url"}
        assert isinstance(result["image_url"], dict)
        assert set(result["image_url"].keys()) == {"url"}
