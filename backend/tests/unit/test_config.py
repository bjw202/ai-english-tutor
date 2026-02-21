"""Unit tests for configuration management.

Tests follow the Arrange-Act-Assert pattern and verify:
- Settings loads from environment variables
- Required fields raise ValidationError when missing
- Default values are applied correctly
- CORS_ORIGINS can be parsed from comma-separated string
"""

import os
from typing import Generator

import pytest
from pydantic import ValidationError

from tutor.config import Settings


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Fixture to provide clean environment for each test.

    Removes environment variables and .env file that might interfere with tests.
    Yields control to the test, then restores environment.
    """
    from pathlib import Path

    # Store original env vars
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "SUPERVISOR_MODEL": os.environ.get("SUPERVISOR_MODEL"),
        "READING_MODEL": os.environ.get("READING_MODEL"),
        "GRAMMAR_MODEL": os.environ.get("GRAMMAR_MODEL"),
        "VOCABULARY_MODEL": os.environ.get("VOCABULARY_MODEL"),
        "HOST": os.environ.get("HOST"),
        "PORT": os.environ.get("PORT"),
        "CORS_ORIGINS": os.environ.get("CORS_ORIGINS"),
        "SESSION_TTL_HOURS": os.environ.get("SESSION_TTL_HOURS"),
    }

    # Clear env vars for clean test
    for key in original_env:
        if original_env[key] is not None:
            del os.environ[key]

    # Temporarily rename .env file to prevent loading
    env_file = Path(".env")
    env_backup = Path(".env.test_backup")
    if env_file.exists():
        env_file.rename(env_backup)

    yield

    # Restore .env file
    if env_backup.exists():
        env_backup.rename(env_file)

    # Restore original env vars
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value


class TestSettingsDefaultValues:
    """Tests for default value assignment in Settings."""

    def test_default_model_settings(self, clean_env: None) -> None:
        """Should apply default values for model configuration when not provided."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        # Act
        settings = Settings()

        # Assert
        assert settings.SUPERVISOR_MODEL == "gpt-4o-mini"
        assert settings.READING_MODEL == "claude-sonnet-4-5"
        assert settings.GRAMMAR_MODEL == "gpt-4o"
        assert settings.VOCABULARY_MODEL == "claude-haiku-4-5"

    def test_default_server_settings(self, clean_env: None) -> None:
        """Should apply default values for server configuration when not provided."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        # Act
        settings = Settings()

        # Assert
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.CORS_ORIGINS == ["http://localhost:3000"]

    def test_default_session_settings(self, clean_env: None) -> None:
        """Should apply default value for session TTL when not provided."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        # Act
        settings = Settings()

        # Assert
        assert settings.SESSION_TTL_HOURS == 24


class TestSettingsRequiredFields:
    """Tests for required field validation in Settings."""

    def test_missing_openai_api_key_raises_error(self, clean_env: None) -> None:
        """Should raise ValidationError when OPENAI_API_KEY is missing."""
        # Arrange - only set ANTHROPIC_API_KEY
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        # Verify error mentions OPENAI_API_KEY
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "OPENAI_API_KEY" in error_fields

    def test_missing_anthropic_api_key_raises_error(self, clean_env: None) -> None:
        """Should raise ValidationError when ANTHROPIC_API_KEY is missing."""
        # Arrange - only set OPENAI_API_KEY
        os.environ["OPENAI_API_KEY"] = "test-openai-key"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        # Verify error mentions ANTHROPIC_API_KEY
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "ANTHROPIC_API_KEY" in error_fields

    def test_missing_both_api_keys_raises_error(self, clean_env: None) -> None:
        """Should raise ValidationError when both API keys are missing."""
        # Arrange - no API keys set

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        # Verify both keys are in error
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "OPENAI_API_KEY" in error_fields
        assert "ANTHROPIC_API_KEY" in error_fields


class TestSettingsFromEnvironment:
    """Tests for loading Settings from environment variables."""

    def test_loads_api_keys_from_environment(self, clean_env: None) -> None:
        """Should load API keys from environment variables."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "env-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "env-anthropic-key"

        # Act
        settings = Settings()

        # Assert
        assert settings.OPENAI_API_KEY == "env-openai-key"
        assert settings.ANTHROPIC_API_KEY == "env-anthropic-key"

    def test_loads_custom_model_from_environment(self, clean_env: None) -> None:
        """Should load custom model settings from environment variables."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
        os.environ["SUPERVISOR_MODEL"] = "custom-supervisor-model"
        os.environ["READING_MODEL"] = "custom-reading-model"
        os.environ["GRAMMAR_MODEL"] = "custom-grammar-model"
        os.environ["VOCABULARY_MODEL"] = "custom-vocab-model"

        # Act
        settings = Settings()

        # Assert
        assert settings.SUPERVISOR_MODEL == "custom-supervisor-model"
        assert settings.READING_MODEL == "custom-reading-model"
        assert settings.GRAMMAR_MODEL == "custom-grammar-model"
        assert settings.VOCABULARY_MODEL == "custom-vocab-model"

    def test_loads_server_settings_from_environment(self, clean_env: None) -> None:
        """Should load server settings from environment variables."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
        os.environ["HOST"] = "127.0.0.1"
        os.environ["PORT"] = "9000"

        # Act
        settings = Settings()

        # Assert
        assert settings.HOST == "127.0.0.1"
        assert settings.PORT == 9000

    def test_loads_session_settings_from_environment(self, clean_env: None) -> None:
        """Should load session TTL from environment variables."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
        os.environ["SESSION_TTL_HOURS"] = "48"

        # Act
        settings = Settings()

        # Assert
        assert settings.SESSION_TTL_HOURS == 48


class TestSettingsCorsOriginsParsing:
    """Tests for CORS_ORIGINS parsing from comma-separated string."""

    def test_single_cors_origin(self, clean_env: None) -> None:
        """Should parse a single CORS origin from string."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
        os.environ["CORS_ORIGINS"] = "http://localhost:3000"

        # Act
        settings = Settings()

        # Assert
        assert settings.CORS_ORIGINS == ["http://localhost:3000"]

    def test_multiple_cors_origins(self, clean_env: None) -> None:
        """Should parse multiple CORS origins from comma-separated string."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
        os.environ["CORS_ORIGINS"] = "http://localhost:3000,https://example.com,https://app.example.com"

        # Act
        settings = Settings()

        # Assert
        assert settings.CORS_ORIGINS == [
            "http://localhost:3000",
            "https://example.com",
            "https://app.example.com",
        ]

    def test_cors_origins_with_spaces(self, clean_env: None) -> None:
        """Should trim whitespace from CORS origins."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
        os.environ["CORS_ORIGINS"] = "http://localhost:3000, https://example.com , https://app.example.com"

        # Act
        settings = Settings()

        # Assert
        assert settings.CORS_ORIGINS == [
            "http://localhost:3000",
            "https://example.com",
            "https://app.example.com",
        ]

    def test_default_cors_origins_when_not_set(self, clean_env: None) -> None:
        """Should use default CORS origins when not provided in environment."""
        # Arrange
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        # Act
        settings = Settings()

        # Assert
        assert settings.CORS_ORIGINS == ["http://localhost:3000"]
