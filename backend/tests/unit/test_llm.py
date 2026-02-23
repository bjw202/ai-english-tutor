"""Unit tests for LLM client factory.

Tests the get_llm() factory function that returns appropriate LangChain LLM clients
based on model name prefix. Claude models raise ValueError; GLM models use
Zhipu AI endpoint via ChatOpenAI.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from tutor.models.llm import get_llm


def _make_mock_settings(openai_key: str = "test-key", glm_key: str | None = None) -> MagicMock:
    """Create a mock settings object for LLM tests."""
    mock = MagicMock()
    mock.OPENAI_API_KEY = openai_key
    mock.GLM_API_KEY = glm_key
    return mock


class TestGetLLM:
    """Test suite for get_llm factory function."""

    def test_returns_chatopenai_for_gpt_models(self) -> None:
        """Test that get_llm returns ChatOpenAI instance for gpt-* models."""
        mock_settings = _make_mock_settings()
        with patch("tutor.models.llm.get_settings", return_value=mock_settings):
            result = get_llm("gpt-4o-mini")

        assert isinstance(result, ChatOpenAI)
        assert result.model_name == "gpt-4o-mini"

    def test_returns_chatopenai_for_gpt_4o(self) -> None:
        """Test that get_llm returns ChatOpenAI for gpt-4o model."""
        mock_settings = _make_mock_settings()
        with patch("tutor.models.llm.get_settings", return_value=mock_settings):
            result = get_llm("gpt-4o")

        assert isinstance(result, ChatOpenAI)
        assert result.model_name == "gpt-4o"

    def test_raises_valueerror_for_claude_models(self) -> None:
        """Test that get_llm raises ValueError for claude-* models (R3)."""
        with pytest.raises(ValueError, match="Claude models are not supported"):
            get_llm("claude-sonnet-4-5")

    def test_raises_valueerror_for_claude_haiku(self) -> None:
        """Test that get_llm raises ValueError for claude-haiku models (R3)."""
        with pytest.raises(ValueError, match="Claude models are not supported"):
            get_llm("claude-haiku-4-5")

    def test_raises_valueerror_for_unknown_models(self) -> None:
        """Test that get_llm raises ValueError for unknown model prefixes."""
        with pytest.raises(ValueError, match="Unknown model"):
            get_llm("unknown-model-x")

    def test_raises_valueerror_for_empty_string(self) -> None:
        """Test that get_llm raises ValueError for empty model name."""
        with pytest.raises(ValueError):
            get_llm("")

    def test_returns_base_chat_model_interface(self) -> None:
        """Test that returned client implements BaseChatModel interface."""
        mock_settings = _make_mock_settings()
        with patch("tutor.models.llm.get_settings", return_value=mock_settings):
            result = get_llm("gpt-4o-mini")

        assert isinstance(result, BaseChatModel)

    def test_chatopenai_has_configured_timeout(self) -> None:
        """Test that ChatOpenAI client is configured with 120s timeout."""
        mock_settings = _make_mock_settings()
        with patch("tutor.models.llm.get_settings", return_value=mock_settings):
            result = get_llm("gpt-4o-mini")

        assert isinstance(result, ChatOpenAI)
        assert result.request_timeout == 120

    def test_chatopenai_has_max_retries_configured(self) -> None:
        """Test that ChatOpenAI client is configured with max_retries=2."""
        mock_settings = _make_mock_settings()
        with patch("tutor.models.llm.get_settings", return_value=mock_settings):
            result = get_llm("gpt-4o-mini")

        assert isinstance(result, ChatOpenAI)
        assert result.max_retries == 2

    def test_glm_returns_chatmodel(self) -> None:
        """Test that GLM models return ChatOpenAI instance (R4)."""
        mock_settings = _make_mock_settings(glm_key="test-glm-key")
        with patch("tutor.models.llm.get_settings", return_value=mock_settings):
            result = get_llm("glm-4v-flash")

        assert isinstance(result, ChatOpenAI)

    def test_glm_uses_zhipu_endpoint(self) -> None:
        """Test that GLM models use Zhipu AI endpoint (R4)."""
        mock_settings = _make_mock_settings(glm_key="test-glm-key")
        with patch("tutor.models.llm.get_settings", return_value=mock_settings):
            result = get_llm("glm-4v")

        assert "bigmodel.cn" in str(result.openai_api_base)

    def test_glm_raises_without_api_key(self) -> None:
        """Test that GLM models raise ValueError when GLM_API_KEY is missing (R5)."""
        mock_settings = _make_mock_settings(glm_key=None)
        with patch("tutor.models.llm.get_settings", return_value=mock_settings):
            with pytest.raises(ValueError, match="GLM_API_KEY"):
                get_llm("glm-4v-flash")

    def test_glm_model_name_preserved(self) -> None:
        """Test that GLM model name is preserved in the ChatOpenAI instance."""
        mock_settings = _make_mock_settings(glm_key="test-glm-key")
        with patch("tutor.models.llm.get_settings", return_value=mock_settings):
            result = get_llm("glm-4v-flash")

        assert result.model_name == "glm-4v-flash"
