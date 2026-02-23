"""LLM client factory for AI English Tutor.

Provides factory function to create LangChain LLM clients configured
with appropriate timeouts and retry logic.

Supported model prefixes:
- gpt-*: OpenAI models (ChatOpenAI)
- glm-*: Zhipu AI GLM models via OpenAI-compatible API (ChatOpenAI + base_url)

Claude models are not supported. Configure model env vars to use gpt-* or glm-* models.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from tutor.config import get_settings


def get_llm(model_name: str, max_tokens: int | None = None, timeout: int = 120) -> BaseChatModel:
    """Get LLM client instance based on model name.

    Factory function that returns the appropriate LangChain LLM client
    based on the model name prefix. Configures each client with a 120-second
    timeout and 2 retries for robustness.

    Args:
        model_name: The model identifier (e.g., "gpt-4o-mini", "glm-4v-flash")
        max_tokens: Maximum tokens for the response. Defaults to 4096.
            Set explicitly to 6144 for reading/vocabulary agents.
        timeout: Request timeout in seconds. Defaults to 120.

    Returns:
        Configured LangChain LLM client instance

    Raises:
        ValueError: If model_name starts with "claude-" (not supported)
        ValueError: If model_name starts with "glm-" but GLM_API_KEY is not configured
        ValueError: If model name prefix is not recognized

    Examples:
        >>> llm = get_llm("gpt-4o-mini")
        >>> isinstance(llm, ChatOpenAI)
        True

        >>> get_llm("claude-sonnet-4-5")
        ValueError: Claude models are not supported. ...

        >>> get_llm("glm-4v-flash")
        # Returns ChatOpenAI with Zhipu AI endpoint when GLM_API_KEY is set
    """
    if model_name.startswith("claude-"):
        raise ValueError(
            f"Claude models are not supported. Use OpenAI or GLM models instead. "
            f"Configure GRAMMAR_MODEL, READING_MODEL, or VOCABULARY_MODEL env vars. "
            f"Got: {model_name}"
        )

    settings = get_settings()

    if model_name.startswith("gpt-"):
        return ChatOpenAI(
            model=model_name,
            timeout=timeout,
            max_retries=2,
            max_tokens=max_tokens if max_tokens is not None else 4096,
            api_key=settings.OPENAI_API_KEY,
            streaming=True,
        )

    if model_name.startswith("glm-"):
        if not settings.GLM_API_KEY:
            raise ValueError(
                f"GLM_API_KEY environment variable is required for GLM models. "
                f"Got model: {model_name}"
            )
        return ChatOpenAI(
            model=model_name,
            timeout=timeout,
            max_retries=2,
            max_tokens=max_tokens if max_tokens is not None else 4096,
            api_key=settings.GLM_API_KEY,
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            streaming=True,
        )

    raise ValueError(f"Unknown model: {model_name}")
