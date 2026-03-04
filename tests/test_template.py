"""Tests for the django-studio cookiecutter template."""

from __future__ import annotations

import py_compile
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

_TEMPLATE_DIR = str(Path(__file__).parent.parent.resolve())

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
            _TEMPLATE_DIR,
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
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "manage.py").exists()

    def test_package_directory_created(self, output_dir, default_context):
        """Test that the package directory is created with correct name."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "testapp").is_dir()

    def test_pyproject_toml_created(self, output_dir, default_context):
        """Test that pyproject.toml is generated."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "pyproject.toml").exists()

    def test_django_settings_created(self, output_dir, default_context):
        """Test that Django config directory is created."""
        cookiecutter(
            _TEMPLATE_DIR,
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
            _TEMPLATE_DIR,
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
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "design").is_dir()

    def test_tailwind_directory_created(self, output_dir, default_context):
        """Test that tailwind directory is included in generated project."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "tailwind").is_dir()

    def test_justfile_created(self, output_dir, default_context):
        """Test that justfile is generated."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "justfile").exists()

    def test_dockerfile_created(self, output_dir, default_context):
        """Test that Dockerfile is generated."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "Dockerfile").exists()

    def test_uv_lock_created(self, output_dir, default_context):
        """Test that uv.lock is generated by the post-gen hook."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / "uv.lock").exists()

    def test_django_studio_skill_installed(self, output_dir, default_context):
        """Test that the django-studio skill is copied to .claude/commands/."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test-project"
        assert (project_path / ".claude" / "commands" / "django-studio.md").exists()


class TestTemplateContent:
    """Test that generated files contain expected content."""

    def test_pyproject_toml_has_correct_package_name(self, output_dir, default_context):
        """Test that pyproject.toml has correct package name."""
        cookiecutter(
            _TEMPLATE_DIR,
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
            _TEMPLATE_DIR,
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
            _TEMPLATE_DIR,
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


class TestFeatureFlagCombinations:
    """Test interactions between feature flags."""

    def test_pwa_with_hx_boost_disabled(self, output_dir):
        """use_pwa=y + use_hx_boost=n: setup_pwa() must patch base.html (not
        default_base.html, which remove_hx_base() already renamed)."""
        project = _render(
            output_dir,
            {**_DEFAULT_CONTEXT, "use_pwa": "y", "use_hx_boost": "n"},
        )
        # hx_base.html must not exist when hx-boost is off
        assert not (project / "templates" / "hx_base.html").exists()
        # default_base.html was renamed to base.html; PWA content goes there
        assert not (project / "templates" / "default_base.html").exists()
        base_content = (project / "templates" / "base.html").read_text()
        assert "manifest" in base_content
        assert "service-worker.js" in base_content
        # Service worker static file must still be present
        assert (project / "static" / "service-worker.js").exists()

    def test_storage_and_i18n_enabled_together(self, output_dir):
        """use_storage=y: storage and i18n (always on) blocks must be present."""
        project = _render(
            output_dir,
            {**_DEFAULT_CONTEXT, "use_storage": "y"},
        )
        settings_content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" in settings_content
        assert "USE_I18N = True" in settings_content
        assert (project / "terraform" / "storage" / "main.tf").exists()
        assert (project / "locale").is_dir()

    def test_all_flags_enabled(self, output_dir):
        """All three flags on: every feature must be wired up."""
        project = _render(
            output_dir,
            {
                **_DEFAULT_CONTEXT,
                "use_hx_boost": "y",
                "use_storage": "y",
                "use_pwa": "y",
            },
        )
        # hx-boost
        assert (project / "templates" / "hx_base.html").exists()
        base_content = (project / "templates" / "base.html").read_text()
        assert "htmx" in base_content
        # PWA patches applied to default_base.html (hx-boost is on)
        default_base_content = (project / "templates" / "default_base.html").read_text()
        assert "manifest" in default_base_content
        assert "service-worker.js" in default_base_content
        assert (project / "static" / "service-worker.js").exists()
        assert "manifest" in (project / "config" / "urls.py").read_text()
        # storage
        assert (project / "terraform" / "storage" / "main.tf").exists()
        settings_content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" in settings_content
        # i18n
        assert (project / "locale").is_dir()
        assert "USE_I18N = True" in settings_content

    def test_all_flags_disabled(self, output_dir):
        """All three optional flags off: none of the optional features must be present."""
        project = _render(
            output_dir,
            {
                **_DEFAULT_CONTEXT,
                "use_hx_boost": "n",
                "use_storage": "n",
                "use_pwa": "n",
            },
        )
        # hx-boost absent
        assert not (project / "templates" / "hx_base.html").exists()
        assert not (project / "templates" / "default_base.html").exists()
        # PWA absent
        assert not (project / "static" / "service-worker.js").exists()
        assert "manifest" not in (project / "config" / "urls.py").read_text()
        # storage absent
        assert not (project / "terraform" / "storage").exists()
        settings_content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" not in settings_content
        # i18n always present
        assert (project / "locale").is_dir()
        assert "USE_I18N = True" in settings_content


class TestRenderedPythonLinting:
    """Verify rendered Python files are syntactically valid and pass linting."""

    def test_python_files_compile(self, project):
        """All rendered .py files must be syntactically valid Python."""
        py_files = list(project.rglob("*.py"))
        assert py_files, "No .py files found in rendered project"
        errors = []
        for py_file in py_files:
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(str(exc))
        assert not errors, "Syntax errors found:\n" + "\n".join(errors)

    def test_python_files_pass_ruff(self, project):
        """All rendered .py files must pass ruff check (F rules)."""
        result = subprocess.run(
            ["ruff", "check", "--select", "F", "--no-cache", str(project)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"ruff check failed:\n{result.stdout}\n{result.stderr}"
        )
