"""LLM client factory for AI English Tutor.

Provides factory function to create LangChain LLM clients configured
with appropriate timeouts and retry logic.
"""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from tutor.config import get_settings


def get_llm(model_name: str) -> BaseChatModel:
    """Get LLM client instance based on model name.

    Factory function that returns the appropriate LangChain LLM client
    based on the model name prefix. Configures each client with a 60-second
    timeout and 2 retries for robustness.

    Args:
        model_name: The model identifier (e.g., "gpt-4o-mini", "claude-sonnet-4-5")

    Returns:
        Configured LangChain LLM client instance

    Raises:
        ValueError: If model name prefix is not recognized

    Examples:
        >>> llm = get_llm("gpt-4o-mini")
        >>> isinstance(llm, ChatOpenAI)
        True

        >>> llm = get_llm("claude-sonnet-4-5")
        >>> isinstance(llm, ChatAnthropic)
        True

        >>> llm = get_llm("unknown-model")
        ValueError: Unknown model: unknown-model
    """
    settings = get_settings()

    if model_name.startswith("gpt-"):
        return ChatOpenAI(
            model=model_name,
            timeout=60,
            max_retries=2,
            api_key=settings.OPENAI_API_KEY,
        )
    if model_name.startswith("claude-"):
        return ChatAnthropic(
            model=model_name,
            timeout=60,
            max_retries=2,
            api_key=settings.ANTHROPIC_API_KEY,
        )
    raise ValueError(f"Unknown model: {model_name}")
