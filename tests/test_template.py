"""Tests for the django-studio copier template."""

from __future__ import annotations

import py_compile
import shutil
import subprocess
import tempfile
from pathlib import Path

import copier
import pytest

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


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    """Render the template once with default context; reused across tests."""
    dst = tmp_path_factory.mktemp("project") / "test_project"
    copier.run_copy(
        src_path=_TEMPLATE_DIR,
        dst_path=str(dst),
        data=_DEFAULT_CONTEXT,
        defaults=True,
        overwrite=True,
        unsafe=True,
        quiet=True,
    )
    return dst


def _render(output_dir: Path, extra_context: dict) -> Path:
    dst = output_dir / "project"
    copier.run_copy(
        src_path=_TEMPLATE_DIR,
        dst_path=str(dst),
        data=extra_context,
        defaults=True,
        overwrite=True,
        unsafe=True,
        quiet=True,
    )
    return dst


class TestTemplateRendering:
    """Test that the copier template renders correctly."""

    def test_template_renders_without_error(self, output_dir):
        result = _render(output_dir, _DEFAULT_CONTEXT)
        assert result.exists()

    def test_manage_py_exists(self, project):
        assert (project / "manage.py").exists()

    def test_package_directory_created(self, project):
        assert (project / "test_project").is_dir()

    def test_pyproject_toml_created(self, project):
        assert (project / "pyproject.toml").exists()

    def test_django_settings_created(self, project):
        assert (project / "config").is_dir()
        assert (project / "config" / "settings.py").exists()

    def test_users_app_created(self, project):
        assert (project / "test_project" / "users").is_dir()
        assert (project / "test_project" / "users" / "apps.py").exists()

    def test_design_directory_created(self, project):
        assert (project / "design").is_dir()

    def test_tailwind_directory_created(self, project):
        assert (project / "tailwind").is_dir()

    def test_justfile_created(self, project):
        assert (project / "justfile").exists()

    def test_dockerfile_created(self, project):
        assert (project / "Dockerfile").exists()

    def test_uv_lock_created(self, project):
        assert (project / "uv.lock").exists()

    def test_copier_answers_file_created(self, project):
        assert (project / ".copier-answers.yml").exists()


class TestTemplateContent:
    """Test that generated files contain expected content."""

    def test_pyproject_toml_has_correct_package_name(self, project):
        content = (project / "pyproject.toml").read_text()
        assert "test_project" in content

    def test_env_example_has_project_slug(self, project):
        content = (project / ".env.example").read_text()
        assert "test_project" in content

    def test_justfile_has_project_slug(self, project):
        content = (project / "justfile").read_text()
        assert '"test_project"' in content

    def test_gha_build_workflow_has_project_slug(self, project):
        content = (project / ".github" / "workflows" / "build.yml").read_text()
        assert "test_project" in content
        assert "PROJECT_SLUG" not in content

    def test_gha_deploy_workflow_has_project_slug(self, project):
        content = (project / ".github" / "workflows" / "deploy.yml").read_text()
        assert "test_project" in content
        assert "PROJECT_SLUG" not in content


class TestProjectNameDerivation:
    """Test that project_slug and package_name are derived from project_name."""

    def test_slug_derived_from_project_name(self, output_dir):
        project = _render(
            output_dir,
            {
                "project_name": "Photo Blog",
                "description": "A photo blog",
                "author": "Author",
                "author_email": "author@example.com",
            },
        )
        assert (project / "photo_blog").is_dir()

    def test_slug_can_be_overridden(self, output_dir):
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
        assert (project / "my_custom_pkg").is_dir()

    def test_empty_project_name_fails(self, output_dir):
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
    """Verify Terraform files are processed correctly."""

    def test_hetzner_variables_has_project_slug(self, project):
        content = (project / "terraform" / "hetzner" / "variables.tf").read_text()
        assert '"test_project"' in content

    def test_hetzner_variables_cluster_name_no_duplicate(self, project):
        content = (project / "terraform" / "hetzner" / "variables.tf").read_text()
        assert content.count('variable "cluster_name"') == 1
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
        assert not (project / "terraform" / "hetzner" / "storage.tf").exists()

    def test_terraform_tfvars_example_has_project_slug(self, project):
        content = (
            project / "terraform" / "hetzner" / "terraform.tfvars.example"
        ).read_text()
        assert "test_project" in content


class TestDomainPrefill:
    """Test that the domain variable is substituted into config files."""

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
                "use_opentelemetry": True,
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
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": True})
        storage = project / "terraform" / "storage"
        assert (storage / "main.tf").exists()
        assert (storage / "variables.tf").exists()
        assert (storage / "outputs.tf").exists()
        assert (storage / "terraform.tfvars.example").exists()
        assert (storage / "README.md").exists()
        assert (storage / ".gitignore").exists()

    def test_storage_dir_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": False})
        assert not (project / "terraform" / "storage").exists()

    def test_s3_settings_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": True})
        content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" in content

    def test_s3_settings_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": False})
        content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" not in content

    def test_env_storage_vars_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": True})
        content = (project / ".env.example").read_text()
        assert "HETZNER_STORAGE_ACCESS_KEY" in content

    def test_env_storage_vars_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": False})
        content = (project / ".env.example").read_text()
        assert "HETZNER_STORAGE_ACCESS_KEY" not in content


class TestPwaFeatureFlag:
    """Test use_pwa flag behaviour."""

    def test_service_worker_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_pwa": True})
        assert (project / "static" / "service-worker.js").exists()

    def test_service_worker_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_pwa": False})
        assert not (project / "static" / "service-worker.js").exists()

    def test_manifest_view_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_pwa": True})
        content = (project / "config" / "urls.py").read_text()
        assert "manifest" in content

    def test_manifest_view_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_pwa": False})
        content = (project / "config" / "urls.py").read_text()
        assert "manifest" not in content


class TestOpenTelemetryFeatureFlag:
    """Test use_opentelemetry flag behaviour."""

    def test_otel_deps_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": True})
        content = (project / "pyproject.toml").read_text()
        assert "opentelemetry-api" in content
        assert "opentelemetry-sdk" in content

    def test_otel_deps_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        content = (project / "pyproject.toml").read_text()
        assert "opentelemetry-api" not in content
        assert "opentelemetry-sdk" not in content

    def test_otel_settings_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": True})
        content = (project / "config" / "settings.py").read_text()
        assert "from opentelemetry" in content
        assert "OPEN_TELEMETRY_URL" in content

    def test_otel_settings_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        content = (project / "config" / "settings.py").read_text()
        assert "from opentelemetry" not in content
        assert "OPEN_TELEMETRY_URL" not in content

    def test_otel_env_vars_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": True})
        content = (project / ".env.example").read_text()
        assert "OPEN_TELEMETRY_URL" in content

    def test_otel_env_vars_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        content = (project / ".env.example").read_text()
        assert "OPEN_TELEMETRY_URL" not in content

    def test_observability_helm_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": True})
        assert (project / "helm" / "observability").is_dir()

    def test_observability_helm_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        assert not (project / "helm" / "observability").exists()

    def test_monitor_node_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": True})
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert 'resource "hcloud_server" "monitor"' in content
        assert 'resource "hcloud_firewall" "monitor"' in content

    def test_monitor_node_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert 'resource "hcloud_server" "monitor"' not in content
        assert 'resource "hcloud_firewall" "monitor"' not in content
        assert "monitor_private_ip" not in content

    def test_monitor_outputs_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": True})
        content = (project / "terraform" / "hetzner" / "outputs.tf").read_text()
        assert '"monitor_public_ip"' in content
        assert '"monitor_private_ip"' in content

    def test_monitor_outputs_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        content = (project / "terraform" / "hetzner" / "outputs.tf").read_text()
        assert '"monitor_public_ip"' not in content
        assert '"monitor_private_ip"' not in content

    def test_cloudflare_grafana_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": True})
        main_content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert 'resource "cloudflare_record" "grafana"' in main_content
        vars_content = (
            project / "terraform" / "cloudflare" / "variables.tf"
        ).read_text()
        assert '"monitor_ip"' in vars_content
        assert '"grafana_subdomain"' in vars_content

    def test_cloudflare_origin_cert_resources_present(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert 'resource "tls_private_key" "origin"' in content
        assert 'resource "tls_cert_request" "origin"' in content
        assert 'resource "cloudflare_origin_ca_certificate" "origin"' in content

    def test_cloudflare_origin_cert_outputs_present(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        content = (project / "terraform" / "cloudflare" / "outputs.tf").read_text()
        assert '"origin_cert_pem"' in content
        assert '"origin_key_pem"' in content

    def test_cloudflare_tls_provider_declared(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert '"hashicorp/tls"' in content

    def test_cloudflare_grafana_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        main_content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert 'resource "cloudflare_record" "grafana"' not in main_content
        vars_content = (
            project / "terraform" / "cloudflare" / "variables.tf"
        ).read_text()
        assert '"monitor_ip"' not in vars_content
        assert '"grafana_subdomain"' not in vars_content

    def test_no_cookiecutter_literals_in_terraform(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_opentelemetry": False})
        for tf_file in (project / "terraform").rglob("*.tf"):
            content = tf_file.read_text()
            assert "cookiecutter" not in content, (
                f"{tf_file} contains cookiecutter literal"
            )


class TestSentryFeatureFlag:
    """Test use_sentry flag behaviour."""

    def test_sentry_dep_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": True})
        content = (project / "pyproject.toml").read_text()
        assert "sentry-sdk" in content

    def test_sentry_dep_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": False})
        content = (project / "pyproject.toml").read_text()
        assert "sentry-sdk" not in content

    def test_sentry_settings_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": True})
        content = (project / "config" / "settings.py").read_text()
        assert "import sentry_sdk" in content
        assert "SENTRY_URL" in content

    def test_sentry_settings_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": False})
        content = (project / "config" / "settings.py").read_text()
        assert "import sentry_sdk" not in content
        assert "SENTRY_URL" not in content

    def test_sentry_env_vars_present_when_enabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": True})
        content = (project / ".env.example").read_text()
        assert "SENTRY_URL" in content

    def test_sentry_env_vars_absent_when_disabled(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_sentry": False})
        content = (project / ".env.example").read_text()
        assert "SENTRY_URL" not in content


class TestFeatureFlagCombinations:
    """Test interactions between feature flags."""

    def test_pwa_enabled_base_html_has_pwa_assets(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_pwa": True})
        assert not (project / "templates" / "hx_base.html").exists()
        assert not (project / "templates" / "default_base.html").exists()
        base_content = (project / "templates" / "base.html").read_text()
        assert "manifest" in base_content
        assert "service-worker.js" in base_content
        assert (project / "static" / "service-worker.js").exists()

    def test_storage_and_i18n_enabled_together(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "use_storage": True})
        settings_content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" in settings_content
        assert "USE_I18N = True" in settings_content
        assert (project / "terraform" / "storage" / "main.tf").exists()
        assert (project / "locale").is_dir()

    def test_all_flags_enabled(self, output_dir):
        project = _render(
            output_dir,
            {
                **_DEFAULT_CONTEXT,
                "use_storage": True,
                "use_pwa": True,
                "use_opentelemetry": True,
                "use_sentry": True,
            },
        )
        assert not (project / "templates" / "hx_base.html").exists()
        assert not (project / "templates" / "default_base.html").exists()
        base_content = (project / "templates" / "base.html").read_text()
        assert "manifest" in base_content
        assert "service-worker.js" in base_content
        assert (project / "static" / "service-worker.js").exists()
        assert "manifest" in (project / "config" / "urls.py").read_text()
        assert (project / "terraform" / "storage" / "main.tf").exists()
        settings_content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" in settings_content
        assert (project / "locale").is_dir()
        assert "USE_I18N = True" in settings_content
        assert "opentelemetry" in settings_content
        assert (project / "helm" / "observability").is_dir()
        pyproject_content = (project / "pyproject.toml").read_text()
        assert "opentelemetry-api" in pyproject_content
        assert "sentry_sdk" in settings_content
        assert "sentry-sdk" in pyproject_content

    def test_all_flags_disabled(self, output_dir):
        project = _render(
            output_dir,
            {
                **_DEFAULT_CONTEXT,
                "use_storage": False,
                "use_pwa": False,
                "use_opentelemetry": False,
                "use_sentry": False,
            },
        )
        assert not (project / "templates" / "hx_base.html").exists()
        assert not (project / "templates" / "default_base.html").exists()
        assert not (project / "static" / "service-worker.js").exists()
        assert "manifest" not in (project / "config" / "urls.py").read_text()
        assert not (project / "terraform" / "storage").exists()
        settings_content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" not in settings_content
        assert (project / "locale").is_dir()
        assert "USE_I18N = True" in settings_content
        assert "opentelemetry" not in settings_content
        assert not (project / "helm" / "observability").exists()
        pyproject_content = (project / "pyproject.toml").read_text()
        assert "opentelemetry-api" not in pyproject_content
        assert "sentry_sdk" not in settings_content
        assert "sentry-sdk" not in pyproject_content


class TestLicensePrompt:
    """Test license prompt behaviour."""

    def test_mit_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "MIT"})
        assert (project / "LICENSE").exists()

    def test_mit_license_content(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "MIT"})
        content = (project / "LICENSE").read_text()
        assert "MIT License" in content
        assert _DEFAULT_CONTEXT["author"] in content

    def test_gpl_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "GPL-3.0"})
        content = (project / "LICENSE").read_text()
        assert "GNU General Public License" in content

    def test_agpl_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "AGPL-3.0"})
        content = (project / "LICENSE").read_text()
        assert "GNU Affero General Public License" in content

    def test_apache_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "Apache-2.0"})
        content = (project / "LICENSE").read_text()
        assert "Apache License" in content

    def test_lgpl_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "LGPL-3.0"})
        content = (project / "LICENSE").read_text()
        assert "GNU Lesser General Public License" in content

    def test_mpl_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "MPL-2.0"})
        content = (project / "LICENSE").read_text()
        assert "Mozilla Public License" in content

    def test_bsd2_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "BSD-2-Clause"})
        content = (project / "LICENSE").read_text()
        assert "BSD 2-Clause" in content

    def test_bsd3_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "BSD-3-Clause"})
        content = (project / "LICENSE").read_text()
        assert "BSD 3-Clause" in content

    def test_isc_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "ISC"})
        content = (project / "LICENSE").read_text()
        assert "ISC License" in content

    def test_eupl_license_file_created(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "EUPL-1.2"})
        content = (project / "LICENSE").read_text()
        assert "European Union Public Licence" in content

    def test_none_license_skips_file(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "None"})
        assert not (project / "LICENSE").exists()

    def test_pyproject_license_set_when_chosen(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "MIT"})
        content = (project / "pyproject.toml").read_text()
        assert 'license = { text = "MIT" }' in content

    def test_pyproject_license_absent_when_none(self, output_dir):
        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "None"})
        content = (project / "pyproject.toml").read_text()
        assert "license" not in content

    def test_license_year_substituted(self, output_dir):
        import datetime

        project = _render(output_dir, {**_DEFAULT_CONTEXT, "license": "MIT"})
        content = (project / "LICENSE").read_text()
        assert str(datetime.date.today().year) in content


class TestClaudeSkillsInstallation:
    """Verify that skills/ are copied to .claude/commands/ by the post-gen hook."""

    def test_dispatcher_installed(self, project):
        assert (project / ".claude" / "commands" / "djstudio.md").exists()

    def test_subcommands_dir_installed(self, project):
        assert (project / ".claude" / "commands" / "djstudio").is_dir()

    def test_subcommand_files_installed(self, project):
        subcommands_dir = project / ".claude" / "commands" / "djstudio"
        installed = {f.name for f in subcommands_dir.iterdir() if f.suffix == ".md"}
        expected = {
            "create-app.md",
            "create-view.md",
            "create-task.md",
            "create-command.md",
            "create-cron.md",
            "create-model.md",
            "help.md",
            "create-crud.md",
            "create-e2e.md",
            "perf.md",
            "secure.md",
            "gdpr.md",
            "a11y.md",
            "deadcode.md",
            "translate.md",
            "launch.md",
            "rotate-secrets.md",
            "sync.md",
            "feedback.md",
        }
        assert expected == installed

    def test_settings_json_installed(self, project):
        assert (project / ".claude" / "settings.json").exists()

    def test_skills_dir_not_in_project_root(self, project):
        assert not (project / "skills").exists()


class TestRenderedPythonLinting:
    """Verify rendered Python files are syntactically valid and pass linting."""

    def test_python_files_compile(self, project):
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
        result = subprocess.run(
            ["ruff", "check", "--select", "F", "--no-cache", str(project)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"ruff check failed:\n{result.stdout}\n{result.stderr}"
        )
