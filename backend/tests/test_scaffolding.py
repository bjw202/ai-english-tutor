"""Scaffolding tests for ai-english-tutor backend package.

These tests verify the basic package structure and configuration
required for the backend system.
"""

import sys
from pathlib import Path

import tomli  # for TOML parsing


class TestPackageStructure:
    """Test that the package structure is correctly created."""

    def test_project_root_exists(self, project_root: Path):
        """Test that the backend project root directory exists."""
        assert project_root.exists()
        assert project_root.is_dir()
        assert (project_root / "pyproject.toml").exists()

    def test_src_directory_exists(self, src_dir: Path):
        """Test that the src directory exists."""
        assert src_dir.exists()
        assert src_dir.is_dir()

    def test_tutor_package_exists(self, src_dir: Path):
        """Test that the tutor package exists."""
        tutor_pkg = src_dir / "tutor"
        assert tutor_pkg.exists()
        assert tutor_pkg.is_dir()
        assert (tutor_pkg / "__init__.py").exists()

    def test_tests_directory_exists(self, tests_dir: Path):
        """Test that the tests directory exists."""
        assert tests_dir.exists()
        assert tests_dir.is_dir()
        assert (tests_dir / "__init__.py").exists()
        assert (tests_dir / "conftest.py").exists()
        assert (tests_dir / "fixtures").exists()
        assert (tests_dir / "fixtures" / "__init__.py").exists()


class TestPyprojectToml:
    """Test that pyproject.toml is correctly configured."""

    def test_pyproject_toml_exists(self, project_root: Path):
        """Test that pyproject.toml exists."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists()
        assert pyproject_path.is_file()

    def test_pyproject_toml_valid(self, project_root: Path):
        """Test that pyproject.toml is valid TOML."""
        pyproject_path = project_root / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)
        assert "project" in data
        assert "dependencies" in data or "dependency-groups" in data

    def test_project_metadata(self, project_root: Path):
        """Test that project metadata is correct."""
        pyproject_path = project_root / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        project = data.get("project", {})
        assert project.get("name") == "ai-english-tutor"
        assert project.get("version") == "0.1.0"
        assert project.get("requires-python") == ">=3.13"

    def test_required_dependencies(self, project_root: Path):
        """Test that all required dependencies are specified."""
        pyproject_path = project_root / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        deps = data.get("project", {}).get("dependencies", [])
        dep_names = {dep.split(">=")[0].split("==")[0].split("<")[0].strip() for dep in deps}

        required = {
            "fastapi",
            "uvicorn[standard]",
            "pydantic",
            "pydantic-settings",
            "langgraph",
            "langchain-openai",
            "python-multipart",
            "pillow",
        }

        for req in required:
            assert req in dep_names, f"Missing required dependency: {req}"

    def test_dev_dependencies(self, project_root: Path):
        """Test that dev dependencies are specified."""
        pyproject_path = project_root / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        # Check in dev dependencies group
        dev_deps = data.get("dependency-groups", {}).get("dev", [])
        dep_names = {dep.split(">=")[0].split("==")[0].split("<")[0].strip() for dep in dev_deps}

        required_dev = {"pytest", "pytest-asyncio", "pytest-cov", "httpx", "ruff"}

        for req in required_dev:
            assert req in dep_names, f"Missing required dev dependency: {req}"

    def test_pytest_configuration(self, project_root: Path):
        """Test that pytest is configured correctly."""
        pyproject_path = project_root / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        tool_config = data.get("tool", {})
        pytest_config = tool_config.get("pytest", {}).get("ini_options", {})

        assert pytest_config.get("asyncio_mode") == "auto"


class TestEnvExample:
    """Test that .env.example is correctly configured."""

    def test_env_example_exists(self, project_root: Path):
        """Test that .env.example exists."""
        env_example = project_root / ".env.example"
        assert env_example.exists()

    def test_env_example_contains_required_vars(self, project_root: Path):
        """Test that .env.example contains all required environment variables."""
        env_example = project_root / ".env.example"
        content = env_example.read_text()

        required_vars = [
            "OPENAI_API_KEY",
            "ENVIRONMENT",
            "LOG_LEVEL",
            "HOST",
            "PORT",
        ]

        for var in required_vars:
            assert var in content, f"Missing environment variable: {var}"


class TestPackageImport:
    """Test that the package can be imported."""

    def test_tutor_package_importable(self, src_dir: Path):
        """Test that the tutor package can be imported."""
        # Add src directory to Python path
        sys.path.insert(0, str(src_dir))

        try:
            import tutor

            assert hasattr(tutor, "__version__")
            assert isinstance(tutor.__version__, str)
        finally:
            sys.path.remove(str(src_dir))

    def test_tutor_package_version_constant(self, src_dir: Path):
        """Test that the tutor package has a version constant."""
        sys.path.insert(0, str(src_dir))

        try:
            import tutor

            # Version should be a valid semantic version
            version = tutor.__version__
            parts = version.split(".")
            assert len(parts) >= 2, "Version should have at least major.minor"
        finally:
            sys.path.remove(str(src_dir))
