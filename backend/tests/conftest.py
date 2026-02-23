"""Pytest configuration and fixtures for ai-english-tutor backend tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def set_test_env():
    """Set test environment variables before each test and reset settings cache."""
    import tutor.config

    # Reset cached settings to ensure test isolation
    tutor.config._settings = None

    # Set required environment variables for testing
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"
    yield
    # Clean up after test
    tutor.config._settings = None
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("CORS_ORIGINS", None)


@pytest.fixture
def project_root() -> Path:
    """Return the backend project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def src_dir(project_root: Path) -> Path:
    """Return the source directory path."""
    return project_root / "src"


@pytest.fixture
def tests_dir(project_root: Path) -> Path:
    """Return the tests directory path."""
    return project_root / "tests"
