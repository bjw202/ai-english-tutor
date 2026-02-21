"""Integration tests for FastAPI endpoints.

Tests all API endpoints following TDD principles.
Tests are written first (RED), then implementation follows (GREEN).
"""

from __future__ import annotations

import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# These imports will fail initially - that's expected in TDD RED phase
# We'll create the modules in GREEN phase


@pytest.fixture
def mock_graph():
    """Mock LangGraph for testing."""
    graph = MagicMock()
    graph.ainvoke = AsyncMock()
    return graph


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing."""
    manager = MagicMock()
    manager.create = MagicMock(return_value="test-session-123")
    manager.get = MagicMock(return_value=None)
    return manager


@pytest.fixture
def app_with_mocks(mock_graph, mock_session_manager):
    """Create FastAPI app with mocked dependencies."""
    # This will be implemented in GREEN phase
    with patch("tutor.routers.tutor.graph", mock_graph), patch(
        "tutor.routers.tutor.session_manager", mock_session_manager
    ):
        from tutor.main import create_app

        app = create_app()
        yield app


@pytest.fixture
def client(app_with_mocks):
    """Test client for FastAPI app."""
    return TestClient(app_with_mocks)


class TestHealthEndpoint:
    """Tests for GET /api/v1/health endpoint."""

    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 status and correct structure."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "openai" in data
        assert "anthropic" in data
        assert "version" in data


class TestAnalyzeEndpoint:
    """Tests for POST /api/v1/tutor/analyze endpoint."""

    def test_analyze_endpoint_streams_sse(self, client, mock_graph, mock_session_manager):
        """Test that analyze endpoint returns SSE stream with correct events."""
        # Mock graph result
        from tutor.schemas import GrammarResult, ReadingResult, VocabularyResult

        mock_graph.ainvoke.return_value = {
            "messages": [],
            "reading_result": ReadingResult(
                summary="Test summary", main_topic="Test topic", emotional_tone="Neutral"
            ),
            "grammar_result": GrammarResult(
                tenses=["past_simple"],
                voice="active",
                sentence_structure="simple",
                analysis="Good grammar",
            ),
            "vocabulary_result": VocabularyResult(
                words=[
                    {
                        "term": "test",
                        "meaning": "a trial",
                        "usage": "This is a test",
                        "synonyms": ["exam"],
                    }
                ]
            ),
        }

        response = client.post(
            "/api/v1/tutor/analyze", json={"text": "This is a test text for analysis.", "level": 3}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse SSE events
        content = response.text
        events = self._parse_sse_events(content)

        # Verify expected events
        event_types = [e["event"] for e in events]
        assert "reading_chunk" in event_types
        assert "grammar_chunk" in event_types
        assert "vocabulary_chunk" in event_types
        assert "done" in event_types

        # Verify session_id in done event
        done_event = next(e for e in events if e["event"] == "done")
        assert "session_id" in done_event["data"]
        assert done_event["data"]["status"] == "complete"

    def test_analyze_endpoint_validates_input(self, client):
        """Test that analyze endpoint validates text length and level range."""
        # Test text too short
        response = client.post("/api/v1/tutor/analyze", json={"text": "short", "level": 3})
        assert response.status_code == 422  # Validation error

        # Test text too long
        long_text = "a" * 5001
        response = client.post(
            "/api/v1/tutor/analyze", json={"text": long_text, "level": 3}
        )
        assert response.status_code == 422

        # Test level out of range
        response = client.post(
            "/api/v1/tutor/analyze", json={"text": "Valid text", "level": 6}
        )
        assert response.status_code == 422

        response = client.post(
            "/api/v1/tutor/analyze", json={"text": "Valid text", "level": 0}
        )
        assert response.status_code == 422

    def _parse_sse_events(self, content: str) -> list[dict]:
        """Helper to parse SSE events from response text."""
        events = []
        lines = content.strip().split("\n")
        current_event = None

        for line in lines:
            if line.startswith("event: "):
                current_event = {"event": line[7:], "data": None}
            elif line.startswith("data: ") and current_event:
                import json

                current_event["data"] = json.loads(line[6:])
                events.append(current_event)
                current_event = None

        return events


class TestAnalyzeImageEndpoint:
    """Tests for POST /api/v1/tutor/analyze-image endpoint."""

    def test_analyze_image_endpoint_streams_sse(self, client, mock_graph, mock_session_manager):
        """Test that analyze-image endpoint processes image and streams SSE."""
        # Mock graph result
        from tutor.schemas import ReadingResult

        mock_graph.ainvoke.return_value = {
            "messages": [],
            "reading_result": ReadingResult(
                summary="Image text summary", main_topic="Image topic", emotional_tone="Neutral"
            ),
            "extracted_text": "Text extracted from image",
        }

        # Valid base64 image (1x1 pixel PNG)
        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        response = client.post(
            "/api/v1/tutor/analyze-image",
            json={
                "image_data": base64_image,
                "mime_type": "image/png",
                "level": 3,
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse SSE events
        content = response.text
        events = self._parse_sse_events(content)

        # Verify events
        event_types = [e["event"] for e in events]
        assert "done" in event_types

    def test_analyze_image_endpoint_rejects_invalid_mime(self, client):
        """Test that analyze-image endpoint rejects invalid MIME types."""
        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        # Invalid MIME type (Pydantic validates Literal types first, returns 422)
        response = client.post(
            "/api/v1/tutor/analyze-image",
            json={
                "image_data": base64_image,
                "mime_type": "image/gif",
                "level": 3,
            },
        )

        # Pydantic validation error (not in allowed Literal values)
        assert response.status_code == 422  # Validation error

    def test_analyze_image_endpoint_rejects_invalid_base64(self, client):
        """Test that analyze-image endpoint rejects invalid base64 data."""
        response = client.post(
            "/api/v1/tutor/analyze-image",
            json={
                "image_data": "not-valid-base64!!!",
                "mime_type": "image/png",
                "level": 3,
            },
        )

        assert response.status_code == 400

    def _parse_sse_events(self, content: str) -> list[dict]:
        """Helper to parse SSE events from response text."""
        events = []
        lines = content.strip().split("\n")
        current_event = None

        for line in lines:
            if line.startswith("event: "):
                current_event = {"event": line[7:], "data": None}
            elif line.startswith("data: ") and current_event:
                import json

                current_event["data"] = json.loads(line[6:])
                events.append(current_event)
                current_event = None

        return events


class TestChatEndpoint:
    """Tests for POST /api/v1/tutor/chat endpoint."""

    def test_chat_endpoint_streams_sse(self, client, mock_graph, mock_session_manager):
        """Test that chat endpoint streams response with SSE."""
        # Mock existing session
        from tutor.schemas import ReadingResult

        mock_session = {
            "id": "existing-session-123",
            "messages": [{"role": "user", "content": "Previous question"}],
        }

        # Override the mock to return an existing session
        mock_session_manager.get = MagicMock(return_value=mock_session)
        mock_session_manager.add_message = MagicMock(return_value=True)

        mock_graph.ainvoke.return_value = {
            "messages": [],
            "reading_result": ReadingResult(
                summary="Chat response", main_topic="Topic", emotional_tone="Neutral"
            ),
        }

        response = client.post(
            "/api/v1/tutor/chat",
            json={
                "session_id": "existing-session-123",
                "question": "What is the meaning of life?",
                "level": 3,
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        content = response.text
        assert "done" in content or "chat_chunk" in content

    def test_chat_endpoint_creates_new_session_if_missing(self, client, mock_graph):
        """Test that chat endpoint creates new session when session_id not found."""
        # Mock session manager to return None (session not found)
        from tutor.routers.tutor import session_manager

        original_get = session_manager.get
        session_manager.get = MagicMock(return_value=None)
        session_manager.create = MagicMock(return_value="new-session-456")

        response = client.post(
            "/api/v1/tutor/chat",
            json={
                "session_id": "non-existent-session",
                "question": "Hello",
                "level": 3,
            },
        )

        assert response.status_code == 200
        session_manager.create.assert_called_once()

        # Restore original
        session_manager.get = original_get

    def test_chat_endpoint_validates_input(self, client):
        """Test that chat endpoint validates input fields."""
        # Missing session_id
        response = client.post(
            "/api/v1/tutor/chat", json={"question": "Hello", "level": 3}
        )
        assert response.status_code == 422

        # Missing question
        response = client.post(
            "/api/v1/tutor/chat", json={"session_id": "test-123", "level": 3}
        )
        assert response.status_code == 422

        # Missing level
        response = client.post(
            "/api/v1/tutor/chat", json={"session_id": "test-123", "question": "Hello"}
        )
        assert response.status_code == 422
