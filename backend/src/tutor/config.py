"""Configuration management for AI English Tutor.

Loads all configuration from environment variables using Pydantic BaseSettings.
Validates required API keys on startup.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Required fields:
        OPENAI_API_KEY: OpenAI API key for LLM access

    Optional fields with defaults:
        GLM_API_KEY: Zhipu AI API key for GLM models (optional)
        SUPERVISOR_MODEL: Model for supervisor agent (default: gpt-4o-mini)
        READING_MODEL: Model for reading comprehension (default: gpt-4o-mini)
        GRAMMAR_MODEL: Model for grammar correction (default: gpt-4o-mini)
        VOCABULARY_MODEL: Model for vocabulary exercises (default: gpt-4o-mini)
        OCR_MODEL: Model for image OCR via OpenAI Vision (default: gpt-4o-mini)
        OCR_DETAIL: Vision API detail level (default: low)
        OCR_MAX_TOKENS: Maximum tokens for OCR response (default: 2048)
        HOST: Server host address (default: 0.0.0.0)
        PORT: Server port (default: 8000)
        CORS_ORIGINS: Comma-separated list of allowed origins (default: http://localhost:3000)
        SESSION_TTL_HOURS: Session time-to-live in hours (default: 24)
    """

    # LLM API Keys
    OPENAI_API_KEY: str
    GLM_API_KEY: str | None = None  # For GLM/Zhipu AI models (optional)

    # Application Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Model Configuration (all gpt-4o-mini for 95% cost reduction)
    SUPERVISOR_MODEL: str = "gpt-4o-mini"
    READING_MODEL: str = "gpt-4o-mini"
    GRAMMAR_MODEL: str = "gpt-4o-mini"
    VOCABULARY_MODEL: str = "gpt-4o-mini"
    OCR_MODEL: str = "gpt-4o-mini"
    OCR_DETAIL: str = "low"
    OCR_MAX_TOKENS: int = 2048

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # Session Configuration
    SESSION_TTL_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",  # Ignore extra fields in .env
    )

    @property
    def CORS_ORIGINS(self) -> list[str]:  # noqa: N802 - Uppercase to match env var convention
        """Get parsed CORS origins list.

        Returns:
            List of parsed origin strings with whitespace trimmed
        """
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


# Global settings instance (lazy initialization)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the global settings instance.

    Uses lazy initialization to avoid loading settings during module import.

    Returns:
        The global Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]  # pydantic-settings reads from env vars
    return _settings


# Backward compatibility: provide a module-level property
class _SettingsProxy:
    """Proxy for lazy settings initialization."""

    def __getattr__(self, name: str):  # noqa: D105
        return getattr(get_settings(), name)

    def __setattr__(self, name: str, value):  # noqa: D105
        setattr(get_settings(), name, value)


settings = _SettingsProxy()
