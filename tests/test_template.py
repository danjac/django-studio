"""Tests for the django-studio cookiecutter template."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter


@pytest.fixture
def output_dir():
    """Create a temporary output directory for rendered templates."""
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def default_context():
    """Default cookiecutter context for testing."""
    return {
        "project_name": "Test Project",
        "project_slug": "test-project",
        "package_name": "testapp",
        "description": "A test project",
        "author": "Test Author",
        "author_email": "test@example.com",
    }


class TestTemplateRendering:
    """Test that the cookiecutter template renders correctly."""

    def test_template_renders_without_error(self, output_dir, default_context):
        """Test that cookiecutter can render the template without errors."""
        result = cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        assert result is not None
        rendered_path = Path(result)
        assert rendered_path.exists()
        assert rendered_path.name == "test-project"

    def test_manage_py_exists(self, output_dir, default_context):
        """Test that manage.py is generated."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "manage.py").exists()

    def test_package_directory_created(self, output_dir, default_context):
        """Test that the package directory is created with correct name."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "testapp").is_dir()

    def test_pyproject_toml_created(self, output_dir, default_context):
        """Test that pyproject.toml is generated."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "pyproject.toml").exists()

    def test_django_settings_created(self, output_dir, default_context):
        """Test that Django config directory is created."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "config").is_dir()
        assert (project_path / "config" / "settings.py").exists()

    def test_users_app_created(self, output_dir, default_context):
        """Test that the users app is created."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "testapp" / "users").is_dir()
        assert (project_path / "testapp" / "users" / "apps.py").exists()

    def test_design_directory_created(self, output_dir, default_context):
        """Test that design directory is included in generated project."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "design").is_dir()

    def test_tailwind_directory_created(self, output_dir, default_context):
        """Test that tailwind directory is included in generated project."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "tailwind").is_dir()

    def test_justfile_created(self, output_dir, default_context):
        """Test that justfile is generated."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "justfile").exists()

    def test_dockerfile_created(self, output_dir, default_context):
        """Test that Dockerfile is generated."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "Dockerfile").exists()


class TestTemplateContent:
    """Test that generated files contain expected content."""

    def test_pyproject_toml_has_correct_package_name(self, output_dir, default_context):
        """Test that pyproject.toml has correct package name."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        pyproject_path = output_dir / "test-project" / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "testapp" in content
        assert "test-project" in content

    def test_env_example_has_project_slug(self, output_dir, default_context):
        """Test that .env.example has correct project slug in OpenTelemetry config."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        env_path = output_dir / "test-project" / ".env.example"
        content = env_path.read_text()
        # The .env.example uses project_slug for OPEN_TELEMETRY_SERVICE_NAME and HETZNER_STORAGE_BUCKET
        assert "test-project" in content


class TestCustomPackageName:
    """Test that custom package names work correctly."""

    def test_custom_package_name(self, output_dir):
        """Test that custom package name is used correctly."""
        context = {
            "project_name": "My App",
            "project_slug": "my-app",
            "package_name": "mypackage",
            "description": "My description",
            "author": "Author",
            "author_email": "author@example.com",
        }

        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=context,
        )

        project_path = output_dir / "my-app"
        assert (project_path / "mypackage").is_dir()
        assert not (project_path / "my-app").exists()
