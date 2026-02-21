"""Unit tests for LLM client factory.

Tests the get_llm() factory function that returns appropriate LangChain LLM clients
based on model name prefix.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from tutor.models.llm import get_llm


class TestGetLLM:
    """Test suite for get_llm factory function."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"})
    def test_returns_chatopenai_for_gpt_models(self) -> None:
        """Test that get_llm returns ChatOpenAI instance for gpt-* models."""
        # Arrange
        model_name = "gpt-4o-mini"

        # Act
        result = get_llm(model_name)

        # Assert
        assert isinstance(result, ChatOpenAI)
        assert result.model_name == model_name

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"})
    def test_returns_chatopenai_for_gpt_4o(self) -> None:
        """Test that get_llm returns ChatOpenAI for gpt-4o model."""
        # Arrange
        model_name = "gpt-4o"

        # Act
        result = get_llm(model_name)

        # Assert
        assert isinstance(result, ChatOpenAI)
        assert result.model_name == model_name

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"})
    def test_returns_chatanthropic_for_claude_models(self) -> None:
        """Test that get_llm returns ChatAnthropic instance for claude-* models."""
        # Arrange
        model_name = "claude-sonnet-4-5"

        # Act
        result = get_llm(model_name)

        # Assert
        assert isinstance(result, ChatAnthropic)
        assert result.model == model_name

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"})
    def test_returns_chatanthropic_for_claude_haiku(self) -> None:
        """Test that get_llm returns ChatAnthropic for claude-haiku-4-5 model."""
        # Arrange
        model_name = "claude-haiku-4-5"

        # Act
        result = get_llm(model_name)

        # Assert
        assert isinstance(result, ChatAnthropic)
        assert result.model == model_name

    def test_raises_valueerror_for_unknown_models(self) -> None:
        """Test that get_llm raises ValueError for unknown model prefixes."""
        # Arrange
        model_name = "unknown-model-x"

        # Act & Assert
        with pytest.raises(ValueError, match=f"Unknown model: {model_name}"):
            get_llm(model_name)

    def test_raises_valueerror_for_empty_string(self) -> None:
        """Test that get_llm raises ValueError for empty model name."""
        # Arrange
        model_name = ""

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown model:"):
            get_llm(model_name)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"})
    def test_returns_base_chat_model_interface(self) -> None:
        """Test that returned client implements BaseChatModel interface."""
        # Arrange
        model_name = "gpt-4o-mini"

        # Act
        result = get_llm(model_name)

        # Assert
        assert isinstance(result, BaseChatModel)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"})
    def test_chatopenai_has_configured_timeout(self) -> None:
        """Test that ChatOpenAI client is configured with timeout."""
        # Arrange
        model_name = "gpt-4o-mini"

        # Act
        result = get_llm(model_name)

        # Assert
        assert isinstance(result, ChatOpenAI)
        assert result.request_timeout == 60

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"})
    def test_chatanthropic_has_configured_timeout(self) -> None:
        """Test that ChatAnthropic client is configured with timeout."""
        # Arrange
        model_name = "claude-sonnet-4-5"

        # Act
        result = get_llm(model_name)

        # Assert
        assert isinstance(result, ChatAnthropic)
        assert result.default_request_timeout == 60

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"})
    def test_chatopenai_has_max_retries_configured(self) -> None:
        """Test that ChatOpenAI client is configured with max_retries."""
        # Arrange
        model_name = "gpt-4o-mini"

        # Act
        result = get_llm(model_name)

        # Assert
        assert isinstance(result, ChatOpenAI)
        assert result.max_retries == 2

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"})
    def test_chatanthropic_has_max_retries_configured(self) -> None:
        """Test that ChatAnthropic client is configured with max_retries."""
        # Arrange
        model_name = "claude-sonnet-4-5"

        # Act
        result = get_llm(model_name)

        # Assert
        assert isinstance(result, ChatAnthropic)
        assert result.max_retries == 2
