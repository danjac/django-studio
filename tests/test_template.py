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
    return output_dir / "test_project"


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
        assert rendered_path.name == "test_project"

    def test_manage_py_exists(self, output_dir, default_context):
        """Test that manage.py is generated."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test_project"
        assert (project_path / "manage.py").exists()

    def test_package_directory_created(self, output_dir, default_context):
        """Test that the package directory is created with correct name."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test_project"
        assert (project_path / "test_project").is_dir()

    def test_pyproject_toml_created(self, output_dir, default_context):
        """Test that pyproject.toml is generated."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test_project"
        assert (project_path / "pyproject.toml").exists()

    def test_django_settings_created(self, output_dir, default_context):
        """Test that Django config directory is created."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test_project"
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

        project_path = output_dir / "test_project"
        assert (project_path / "test_project" / "users").is_dir()
        assert (project_path / "test_project" / "users" / "apps.py").exists()

    def test_design_directory_created(self, output_dir, default_context):
        """Test that design directory is included in generated project."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test_project"
        assert (project_path / "design").is_dir()

    def test_tailwind_directory_created(self, output_dir, default_context):
        """Test that tailwind directory is included in generated project."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test_project"
        assert (project_path / "tailwind").is_dir()

    def test_justfile_created(self, output_dir, default_context):
        """Test that justfile is generated."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test_project"
        assert (project_path / "justfile").exists()

    def test_dockerfile_created(self, output_dir, default_context):
        """Test that Dockerfile is generated."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test_project"
        assert (project_path / "Dockerfile").exists()

    def test_uv_lock_created(self, output_dir, default_context):
        """Test that uv.lock is generated by the post-gen hook."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        project_path = output_dir / "test_project"
        assert (project_path / "uv.lock").exists()


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

        pyproject_path = output_dir / "test_project" / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "test_project" in content
        assert "test_project" in content

    def test_env_example_has_project_slug(self, output_dir, default_context):
        """Test that .env.example has correct project slug."""
        cookiecutter(
            _TEMPLATE_DIR,
            no_input=True,
            output_dir=str(output_dir),
            extra_context=default_context,
        )

        env_path = output_dir / "test_project" / ".env.example"
        content = env_path.read_text()
        # project_slug appears in HETZNER_STORAGE_BUCKET and OPEN_TELEMETRY_SERVICE_NAME
        assert "test_project" in content


class TestProjectNameDerivation:
    """Test that project_slug and package_name are derived from project_name."""

    def test_slug_and_package_derived_from_project_name(self, output_dir):
        """Providing only project_name derives slug and package automatically."""
        project = _render(
            output_dir,
            {
                "project_name": "Photo Blog",
                "description": "A photo blog",
                "author": "Author",
                "author_email": "author@example.com",
            },
        )
        assert project.name == "photo_blog"
        assert (project / "photo_blog").is_dir()

    def test_slug_and_package_can_be_overridden(self, output_dir):
        """Explicit project_slug and package_name override the derived values."""
        project = _render(
            output_dir,
            {
                "project_name": "My App",
                "project_slug": "my_custom_slug",
                "package_name": "my_custom_pkg",
                "description": "My description",
                "author": "Author",
                "author_email": "author@example.com",
            },
        )
        assert project.name == "my_custom_slug"
        assert (project / "my_custom_pkg").is_dir()

    def test_empty_project_name_fails(self, output_dir):
        """Generation must fail fast when project_name is empty."""
        with pytest.raises(Exception):
            _render(
                output_dir,
                {
                    "project_name": "",
                    "description": "A test",
                    "author": "Author",
                    "author_email": "author@example.com",
                },
            )


class TestTerraformRendering:
    """Verify Terraform files are processed correctly by cookiecutter.

    These files were previously excluded from rendering via _copy_without_render.
    """

    def test_hetzner_variables_has_project_slug(self, project):
        content = (project / "terraform" / "hetzner" / "variables.tf").read_text()
        assert '"test_project"' in content

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
        # bucket_name default lives in variables.tf, not main.tf
        content = (project / "terraform" / "storage" / "variables.tf").read_text()
        assert "test_project-media" in content

    def test_storage_no_cookiecutter_literals(self, project):
        for tf_file in (project / "terraform" / "storage").glob("*.tf"):
            content = tf_file.read_text()
            assert "cookiecutter" not in content, (
                f"{tf_file} contains cookiecutter literal"
            )

    def test_storage_variables_tf_exists(self, project):
        assert (project / "terraform" / "storage" / "variables.tf").exists()

    def test_storage_outputs_tf_exists(self, project):
        assert (project / "terraform" / "storage" / "outputs.tf").exists()

    def test_storage_tfvars_example_exists(self, project):
        assert (project / "terraform" / "storage" / "terraform.tfvars.example").exists()

    def test_storage_readme_exists(self, project):
        assert (project / "terraform" / "storage" / "README.md").exists()

    def test_storage_gitignore_exists(self, project):
        assert (project / "terraform" / "storage" / ".gitignore").exists()

    def test_storage_main_has_required_version(self, project):
        content = (project / "terraform" / "storage" / "main.tf").read_text()
        assert 'required_version = ">= 1.0"' in content

    def test_storage_main_has_no_inlined_variables(self, project):
        content = (project / "terraform" / "storage" / "main.tf").read_text()
        assert 'variable "access_key"' not in content
        assert 'variable "secret_key"' not in content
        assert 'variable "bucket_name"' not in content
        assert 'variable "location"' not in content

    def test_storage_main_has_no_inlined_outputs(self, project):
        content = (project / "terraform" / "storage" / "main.tf").read_text()
        assert 'output "bucket_name"' not in content
        assert 'output "endpoint_url"' not in content

    def test_storage_variables_has_all_variables(self, project):
        content = (project / "terraform" / "storage" / "variables.tf").read_text()
        assert 'variable "access_key"' in content
        assert 'variable "secret_key"' in content
        assert 'variable "bucket_name"' in content
        assert 'variable "location"' in content

    def test_storage_outputs_has_both_outputs(self, project):
        content = (project / "terraform" / "storage" / "outputs.tf").read_text()
        assert 'output "bucket_name"' in content
        assert 'output "endpoint_url"' in content

    def test_storage_tfvars_example_has_project_slug(self, project):
        content = (
            project / "terraform" / "storage" / "terraform.tfvars.example"
        ).read_text()
        assert "test_project-media" in content

    def test_storage_tfvars_example_no_cookiecutter_literals(self, project):
        content = (
            project / "terraform" / "storage" / "terraform.tfvars.example"
        ).read_text()
        assert "cookiecutter" not in content

    def test_storage_not_in_hetzner_module(self, project):
        """storage.tf must not live alongside the cluster variables - it was
        moved to terraform/storage/ to avoid duplicate variable declarations."""
        assert not (project / "terraform" / "hetzner" / "storage.tf").exists()

    def test_terraform_tfvars_example_has_project_slug(self, project):
        content = (
            project / "terraform" / "hetzner" / "terraform.tfvars.example"
        ).read_text()
        assert "test_project" in content


class TestDomainPrefill:
    """Test that the domain cookiecutter variable is substituted into config files."""

    def test_cloudflare_tfvars_has_domain(self, output_dir):
        project = _render(
            output_dir, {**_DEFAULT_CONTEXT, "domain": "myapp.example.org"}
        )
        content = (
            project / "terraform" / "cloudflare" / "terraform.tfvars.example"
        ).read_text()
        assert 'domain = "myapp.example.org"' in content

    def test_cloudflare_tfvars_default_domain(self, output_dir):
        project = _render(output_dir, _DEFAULT_CONTEXT)
        content = (
            project / "terraform" / "cloudflare" / "terraform.tfvars.example"
        ).read_text()
        assert 'domain = "example.com"' in content

    def test_helm_site_values_has_domain(self, output_dir):
        project = _render(
            output_dir, {**_DEFAULT_CONTEXT, "domain": "myapp.example.org"}
        )
        content = (project / "helm" / "site" / "values.secret.yaml.example").read_text()
        assert 'domain: "myapp.example.org"' in content
        assert 'allowedHosts: ".myapp.example.org"' in content

    def test_helm_site_values_no_change_me_for_domain(self, output_dir):
        """domain and allowedHosts must not contain CHANGE_ME after rendering."""
        project = _render(
            output_dir, {**_DEFAULT_CONTEXT, "domain": "myapp.example.org"}
        )
        content = (project / "helm" / "site" / "values.secret.yaml.example").read_text()
        lines = {line.strip() for line in content.splitlines()}
        assert not any(
            "CHANGE_ME" in line
            for line in lines
            if "domain" in line or "allowedHosts" in line
        )

    def test_helm_observability_grafana_host_has_domain(self, output_dir):
        project = _render(
            output_dir,
            {
                **_DEFAULT_CONTEXT,
                "domain": "myapp.example.org",
                "use_opentelemetry": "y",
            },
        )
        content = (
            project / "helm" / "observability" / "values.secret.yaml.example"
        ).read_text()
        assert "grafana.myapp.example.org" in content

    def test_no_cookiecutter_literals_in_domain_fields(self, output_dir):
        project = _render(
            output_dir, {**_DEFAULT_CONTEXT, "domain": "myapp.example.org"}
        )
        content = (project / "helm" / "site" / "values.secret.yaml.example").read_text()
        assert "cookiecutter" not in content
        content = (
            project / "terraform" / "cloudflare" / "terraform.tfvars.example"
        ).read_text()
        assert "cookiecutter" not in content


class TestStorageFeatureFlag:
    """Test use_storage flag behaviour."""

    def test_storage_dir_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": "y"})
        storage = project / "terraform" / "storage"
        assert (storage / "main.tf").exists()
        assert (storage / "variables.tf").exists()
        assert (storage / "outputs.tf").exists()
        assert (storage / "terraform.tfvars.example").exists()
        assert (storage / "README.md").exists()
        assert (storage / ".gitignore").exists()

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

    def test_base_html_contains_full_html_when_disabled(self, output_dir):
        """default_base.html must be renamed (not just deleted) into base.html.

        This test guards against the Path.move() crash (pathlib.Path has no
        .move() method) that previously caused every use_hx_boost=n project
        generation to fail.
        """
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_hx_boost": "n"})
        content = (project / "templates" / "base.html").read_text()
        # The full layout from default_base.html starts with a doctype; the
        # old extends-stub did not.
        assert "<!doctype html>" in content
        assert "extends" not in content


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


class TestOpenTelemetryFeatureFlag:
    """Test use_opentelemetry flag behaviour."""

    def test_otel_deps_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "y"})
        content = (project / "pyproject.toml").read_text()
        assert "opentelemetry-api" in content
        assert "opentelemetry-sdk" in content

    def test_otel_deps_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        content = (project / "pyproject.toml").read_text()
        assert "opentelemetry-api" not in content
        assert "opentelemetry-sdk" not in content

    def test_otel_settings_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "y"})
        content = (project / "config" / "settings.py").read_text()
        assert "from opentelemetry" in content
        assert "OPEN_TELEMETRY_URL" in content

    def test_otel_settings_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        content = (project / "config" / "settings.py").read_text()
        assert "from opentelemetry" not in content
        assert "OPEN_TELEMETRY_URL" not in content

    def test_otel_env_vars_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "y"})
        content = (project / ".env.example").read_text()
        assert "OPEN_TELEMETRY_URL" in content

    def test_otel_env_vars_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        content = (project / ".env.example").read_text()
        assert "OPEN_TELEMETRY_URL" not in content

    def test_observability_helm_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "y"})
        assert (project / "helm" / "observability").is_dir()

    def test_observability_helm_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        assert not (project / "helm" / "observability").exists()

    def test_monitor_node_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "y"})
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert 'resource "hcloud_server" "monitor"' in content
        assert 'resource "hcloud_firewall" "monitor"' in content

    def test_monitor_node_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert 'resource "hcloud_server" "monitor"' not in content
        assert 'resource "hcloud_firewall" "monitor"' not in content
        assert "monitor_private_ip" not in content

    def test_monitor_outputs_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "y"})
        content = (project / "terraform" / "hetzner" / "outputs.tf").read_text()
        assert '"monitor_public_ip"' in content
        assert '"monitor_private_ip"' in content

    def test_monitor_outputs_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        content = (project / "terraform" / "hetzner" / "outputs.tf").read_text()
        assert '"monitor_public_ip"' not in content
        assert '"monitor_private_ip"' not in content

    def test_cloudflare_grafana_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "y"})
        main_content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert 'resource "cloudflare_record" "grafana"' in main_content
        vars_content = (
            project / "terraform" / "cloudflare" / "variables.tf"
        ).read_text()
        assert '"monitor_ip"' in vars_content
        assert '"grafana_subdomain"' in vars_content

    def test_cloudflare_origin_cert_resources_present(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert 'resource "tls_private_key" "origin"' in content
        assert 'resource "tls_cert_request" "origin"' in content
        assert 'resource "cloudflare_origin_ca_certificate" "origin"' in content

    def test_cloudflare_origin_cert_outputs_present(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        content = (project / "terraform" / "cloudflare" / "outputs.tf").read_text()
        assert '"origin_cert_pem"' in content
        assert '"origin_key_pem"' in content

    def test_cloudflare_tls_provider_declared(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert '"hashicorp/tls"' in content

    def test_cloudflare_grafana_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        main_content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert 'resource "cloudflare_record" "grafana"' not in main_content
        vars_content = (
            project / "terraform" / "cloudflare" / "variables.tf"
        ).read_text()
        assert '"monitor_ip"' not in vars_content
        assert '"grafana_subdomain"' not in vars_content

    def test_no_cookiecutter_literals_in_terraform(self, output_dir):
        """Rendered terraform files must not contain cookiecutter template tags."""
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": "n"})
        for tf_file in (project / "terraform").rglob("*.tf"):
            content = tf_file.read_text()
            assert "cookiecutter" not in content, (
                f"{tf_file} contains cookiecutter literal"
            )


class TestSentryFeatureFlag:
    """Test use_sentry flag behaviour."""

    def test_sentry_dep_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": "y"})
        content = (project / "pyproject.toml").read_text()
        assert "sentry-sdk" in content

    def test_sentry_dep_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": "n"})
        content = (project / "pyproject.toml").read_text()
        assert "sentry-sdk" not in content

    def test_sentry_settings_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": "y"})
        content = (project / "config" / "settings.py").read_text()
        assert "import sentry_sdk" in content
        assert "SENTRY_URL" in content

    def test_sentry_settings_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": "n"})
        content = (project / "config" / "settings.py").read_text()
        assert "import sentry_sdk" not in content
        assert "SENTRY_URL" not in content

    def test_sentry_env_vars_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": "y"})
        content = (project / ".env.example").read_text()
        assert "SENTRY_URL" in content

    def test_sentry_env_vars_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": "n"})
        content = (project / ".env.example").read_text()
        assert "SENTRY_URL" not in content


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
        """All flags on: every feature must be wired up."""
        project = _render(
            output_dir,
            {
                **_DEFAULT_CONTEXT,
                "use_hx_boost": "y",
                "use_storage": "y",
                "use_pwa": "y",
                "use_opentelemetry": "y",
                "use_sentry": "y",
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
        # opentelemetry
        assert "opentelemetry" in settings_content
        assert (project / "helm" / "observability").is_dir()
        pyproject_content = (project / "pyproject.toml").read_text()
        assert "opentelemetry-api" in pyproject_content
        # sentry
        assert "sentry_sdk" in settings_content
        assert "sentry-sdk" in pyproject_content

    def test_all_flags_disabled(self, output_dir):
        """All optional flags off: none of the optional features must be present."""
        project = _render(
            output_dir,
            {
                **_DEFAULT_CONTEXT,
                "use_hx_boost": "n",
                "use_storage": "n",
                "use_pwa": "n",
                "use_opentelemetry": "n",
                "use_sentry": "n",
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
        # opentelemetry absent
        assert "opentelemetry" not in settings_content
        assert not (project / "helm" / "observability").exists()
        pyproject_content = (project / "pyproject.toml").read_text()
        assert "opentelemetry-api" not in pyproject_content
        # sentry absent
        assert "sentry_sdk" not in settings_content
        assert "sentry-sdk" not in pyproject_content


class TestClaudeSkillsInstallation:
    """Verify that skills/ are copied to .claude/commands/ by the post-gen hook."""

    def test_dispatcher_installed(self, project):
        """djstudio.md dispatcher must be present in .claude/commands/."""
        assert (project / ".claude" / "commands" / "djstudio.md").exists()

    def test_subcommands_dir_installed(self, project):
        """djstudio/ subcommands directory must be present in .claude/commands/."""
        assert (project / ".claude" / "commands" / "djstudio").is_dir()

    def test_subcommand_files_installed(self, project):
        """All subcommand files must be copied from skills/djstudio/."""
        subcommands_dir = project / ".claude" / "commands" / "djstudio"
        installed = {f.name for f in subcommands_dir.iterdir() if f.suffix == ".md"}
        expected = {
            "create-app.md",
            "create-view.md",
            "create-task.md",
            "create-model.md",
            "create-crud.md",
            "create-e2e.md",
            "secure.md",
            "gdpr.md",
            "translate.md",
            "launch.md",
            "feedback.md",
        }
        assert expected == installed

    def test_settings_json_installed(self, project):
        """.claude/settings.json must be written by install_claude_hooks()."""
        assert (project / ".claude" / "settings.json").exists()

    def test_skills_dir_not_in_project_root(self, project):
        """The source skills/ directory must not be copied to the project root."""
        assert not (project / "skills").exists()


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
