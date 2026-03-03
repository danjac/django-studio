"""Tests for the django-studio cookiecutter template."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

_TEMPLATE_DIR = "."

_DEFAULT_CONTEXT = {
    "project_name": "Test Project",
    "project_slug": "test-project",
    "package_name": "testapp",
    "description": "A test project",
    "author": "Test Author",
    "author_email": "test@example.com",
}


@pytest.fixture
def output_dir():
    """Create a temporary output directory for rendered templates."""
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def default_context():
    """Default cookiecutter context for testing."""
    return _DEFAULT_CONTEXT


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    """Render the template once with default context; reused across tests."""
    output_dir = tmp_path_factory.mktemp("project")
    cookiecutter(
        _TEMPLATE_DIR,
        no_input=True,
        output_dir=str(output_dir),
        extra_context=_DEFAULT_CONTEXT,
    )
    return output_dir / "test-project"


def _render(output_dir: Path, extra_context: dict) -> Path:
    result = cookiecutter(
        _TEMPLATE_DIR,
        no_input=True,
        output_dir=str(output_dir),
        extra_context=extra_context,
    )
    return Path(result)


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

    def test_uv_lock_created(self, output_dir, default_context):
        """Test that uv.lock is generated by the post-gen hook."""
        cookiecutter(
            ".",
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "uv.lock").exists()


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


class TestTerraformRendering:
    """Verify Terraform files are processed correctly by cookiecutter.

    These files were previously excluded from rendering via _copy_without_render.
    """

    def test_hetzner_variables_has_project_slug(self, project):
        content = (project / "terraform" / "hetzner" / "variables.tf").read_text()
        assert '"test-project"' in content

    def test_hetzner_variables_cluster_name_no_duplicate(self, project):
        """The cluster_name variable must not have duplicate attribute declarations."""
        content = (project / "terraform" / "hetzner" / "variables.tf").read_text()
        assert content.count('variable "cluster_name"') == 1
        # Extract the cluster_name block and verify it has exactly one default
        start = content.index('variable "cluster_name"')
        end = content.index("}", start) + 1
        block = content[start:end]
        assert block.count("default") == 1

    def test_hetzner_variables_no_cookiecutter_literals(self, project):
        content = (project / "terraform" / "hetzner" / "variables.tf").read_text()
        assert "cookiecutter" not in content

    def test_storage_module_exists(self, project):
        assert (project / "terraform" / "storage" / "main.tf").exists()

    def test_storage_has_project_slug(self, project):
        content = (project / "terraform" / "storage" / "main.tf").read_text()
        assert "test-project-media" in content

    def test_storage_no_cookiecutter_literals(self, project):
        content = (project / "terraform" / "storage" / "main.tf").read_text()
        assert "cookiecutter" not in content

    def test_storage_not_in_hetzner_module(self, project):
        """storage.tf must not live alongside the cluster variables - it was
        moved to terraform/storage/ to avoid duplicate variable declarations."""
        assert not (project / "terraform" / "hetzner" / "storage.tf").exists()

    def test_terraform_tfvars_example_has_project_slug(self, project):
        content = (
            project / "terraform" / "hetzner" / "terraform.tfvars.example"
        ).read_text()
        assert "test-project" in content


class TestStorageFeatureFlag:
    """Test use_storage flag behaviour."""

    def test_storage_dir_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": "y"})
        assert (project / "terraform" / "storage" / "main.tf").exists()

    def test_storage_dir_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": "n"})
        assert not (project / "terraform" / "storage").exists()

    def test_s3_settings_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": "y"})
        content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" in content

    def test_s3_settings_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": "n"})
        content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" not in content

    def test_env_storage_vars_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": "y"})
        content = (project / ".env.example").read_text()
        assert "HETZNER_STORAGE_ACCESS_KEY" in content

    def test_env_storage_vars_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": "n"})
        content = (project / ".env.example").read_text()
        assert "HETZNER_STORAGE_ACCESS_KEY" not in content


class TestHxBoostFeatureFlag:
    """Test use_hx_boost flag behaviour."""

    def test_hx_base_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_hx_boost": "y"})
        assert (project / "templates" / "hx_base.html").exists()

    def test_hx_base_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_hx_boost": "n"})
        assert not (project / "templates" / "hx_base.html").exists()

    def test_base_html_uses_htmx_extends_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_hx_boost": "y"})
        content = (project / "templates" / "base.html").read_text()
        assert "htmx" in content

    def test_base_html_is_full_layout_when_disabled(self, output_dir):
        """Without hx-boost, base.html should be the full layout (no dynamic extends)."""
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_hx_boost": "n"})
        assert (project / "templates" / "base.html").exists()
        assert not (project / "templates" / "default_base.html").exists()


class TestI18nFeatureFlag:
    """Test use_i18n flag behaviour."""

    def test_locale_dir_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_i18n": "y"})
        assert (project / "locale").is_dir()

    def test_locale_dir_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_i18n": "n"})
        assert not (project / "locale").exists()

    def test_use_i18n_true_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_i18n": "y"})
        content = (project / "config" / "settings.py").read_text()
        assert "USE_I18N = True" in content

    def test_use_i18n_false_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_i18n": "n"})
        content = (project / "config" / "settings.py").read_text()
        assert "USE_I18N = False" in content


class TestPwaFeatureFlag:
    """Test use_pwa flag behaviour."""

    def test_service_worker_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_pwa": "y"})
        assert (project / "static" / "service-worker.js").exists()

    def test_service_worker_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_pwa": "n"})
        assert not (project / "static" / "service-worker.js").exists()

    def test_manifest_view_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_pwa": "y"})
        content = (project / "config" / "urls.py").read_text()
        assert "manifest" in content

    def test_manifest_view_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_pwa": "n"})
        content = (project / "config" / "urls.py").read_text()
        assert "manifest" not in content
