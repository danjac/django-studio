"""Tests on the shared rendered project: structure, content, terraform, features, skills."""

from __future__ import annotations

import py_compile
import subprocess


class TestProjectStructure:
    """Test that the rendered project has the expected file structure."""

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

    def test_root_app_has_apps_py(self, project):
        assert (project / "test_project" / "apps.py").exists()

    def test_root_app_has_management_command(self, project):
        cmd = (
            project / "test_project" / "management" / "commands" / "set_default_site.py"
        )
        assert cmd.exists()

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


class TestProjectContent:
    """Test that generated files contain expected content."""

    def test_pyproject_toml_has_correct_package_name(self, project):
        content = (project / "pyproject.toml").read_text()
        assert "test_project" in content

    def test_justfile_has_project_slug(self, project):
        content = (project / "justfile").read_text()
        assert '"test_project"' in content

    def test_root_apps_py_has_correct_class_name(self, project):
        content = (project / "test_project" / "apps.py").read_text()
        assert "class TestProjectConfig(AppConfig):" in content

    def test_root_apps_py_has_correct_name(self, project):
        content = (project / "test_project" / "apps.py").read_text()
        assert 'name = "test_project"' in content

    def test_root_app_in_installed_apps(self, project):
        content = (project / "config" / "settings.py").read_text()
        assert '"test_project",' in content

    def test_gha_build_workflow_has_project_slug(self, project):
        content = (project / ".github" / "workflows" / "build.yml").read_text()
        assert "test_project" in content
        assert "PROJECT_SLUG" not in content

    def test_gha_deploy_workflow_has_project_slug(self, project):
        content = (project / ".github" / "workflows" / "deploy.yml").read_text()
        assert "test_project" in content
        assert "PROJECT_SLUG" not in content


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

    def test_backups_module_exists(self, project):
        assert (project / "terraform" / "backups" / "main.tf").exists()

    def test_backups_has_project_slug(self, project):
        content = (project / "terraform" / "backups" / "variables.tf").read_text()
        assert "test_project-db-backups" in content

    def test_backups_no_cookiecutter_literals(self, project):
        for tf_file in (project / "terraform" / "backups").glob("*.tf"):
            content = tf_file.read_text()
            assert "cookiecutter" not in content, (
                f"{tf_file} contains cookiecutter literal"
            )

    def test_backups_variables_tf_exists(self, project):
        assert (project / "terraform" / "backups" / "variables.tf").exists()

    def test_backups_outputs_tf_exists(self, project):
        assert (project / "terraform" / "backups" / "outputs.tf").exists()

    def test_backups_tfvars_example_exists(self, project):
        assert (project / "terraform" / "backups" / "terraform.tfvars.example").exists()

    def test_backups_readme_exists(self, project):
        assert (project / "terraform" / "backups" / "README.md").exists()

    def test_backups_gitignore_exists(self, project):
        assert (project / "terraform" / "backups" / ".gitignore").exists()

    def test_backups_main_has_private_acl(self, project):
        content = (project / "terraform" / "backups" / "main.tf").read_text()
        assert 'acl    = "private"' in content

    def test_backups_main_has_required_version(self, project):
        content = (project / "terraform" / "backups" / "main.tf").read_text()
        assert 'required_version = ">= 1.0"' in content

    def test_backups_variables_has_all_variables(self, project):
        content = (project / "terraform" / "backups" / "variables.tf").read_text()
        assert 'variable "access_key"' in content
        assert 'variable "secret_key"' in content
        assert 'variable "bucket_name"' in content
        assert 'variable "location"' in content

    def test_backups_outputs_has_both_outputs(self, project):
        content = (project / "terraform" / "backups" / "outputs.tf").read_text()
        assert 'output "bucket_name"' in content
        assert 'output "endpoint_url"' in content

    def test_backups_tfvars_example_has_project_slug(self, project):
        content = (
            project / "terraform" / "backups" / "terraform.tfvars.example"
        ).read_text()
        assert "test_project-db-backups" in content

    def test_backups_separate_from_media(self, project):
        """Backup bucket name must differ from media bucket name."""
        backups = (
            project / "terraform" / "backups" / "terraform.tfvars.example"
        ).read_text()
        media = (
            project / "terraform" / "storage" / "terraform.tfvars.example"
        ).read_text()
        assert "db-backups" in backups
        assert "db-backups" not in media


class TestAlwaysIncludedFeatures:
    """Verify that storage, PWA, observability, Sentry, and backups are always present."""

    def test_storage_terraform_always_present(self, project):
        storage = project / "terraform" / "storage"
        assert (storage / "main.tf").exists()
        assert (storage / "variables.tf").exists()
        assert (storage / "outputs.tf").exists()

    def test_s3_settings_always_present(self, project):
        content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" in content

    def test_pwa_service_worker_always_present(self, project):
        assert (project / "static" / "service-worker.js").exists()

    def test_pwa_manifest_in_urls(self, project):
        content = (project / "config" / "urls.py").read_text()
        assert "manifest" in content

    def test_pwa_assets_in_base_html(self, project):
        content = (project / "templates" / "base.html").read_text()
        assert "manifest" in content
        assert "service-worker.js" in content

    def test_observability_helm_always_present(self, project):
        assert (project / "helm" / "observability").is_dir()

    def test_otel_deps_always_present(self, project):
        content = (project / "pyproject.toml").read_text()
        assert "opentelemetry-api" in content
        assert "opentelemetry-sdk" in content

    def test_otel_settings_always_present(self, project):
        content = (project / "config" / "settings.py").read_text()
        assert "from opentelemetry" in content
        assert "OPEN_TELEMETRY_URL" in content

    def test_monitor_node_always_present(self, project):
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert 'resource "hcloud_server" "monitor"' in content
        assert 'resource "hcloud_firewall" "monitor"' in content

    def test_monitor_outputs_always_present(self, project):
        content = (project / "terraform" / "hetzner" / "outputs.tf").read_text()
        assert '"monitor_public_ip"' in content
        assert '"monitor_private_ip"' in content

    def test_cloudflare_grafana_always_present(self, project):
        content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert 'resource "cloudflare_record" "grafana"' in content
        vars_content = (
            project / "terraform" / "cloudflare" / "variables.tf"
        ).read_text()
        assert '"monitor_ip"' in vars_content
        assert '"grafana_subdomain"' in vars_content

    def test_sentry_dep_always_present(self, project):
        content = (project / "pyproject.toml").read_text()
        assert "sentry-sdk" in content

    def test_sentry_settings_always_present(self, project):
        content = (project / "config" / "settings.py").read_text()
        assert "import sentry_sdk" in content
        assert "SENTRY_URL" in content

    def test_no_jinja_conditionals_remaining(self, project):
        """Ensure no feature-flag Jinja2 conditionals leaked into generated files."""
        for path in project.rglob("*.py"):
            content = path.read_text()
            assert "{%- if use_" not in content, f"{path} contains Jinja2 conditional"
        for path in project.rglob("*.toml"):
            content = path.read_text()
            assert "{%- if use_" not in content, f"{path} contains Jinja2 conditional"

    def test_no_cookiecutter_literals_in_terraform(self, project):
        for tf_file in (project / "terraform").rglob("*.tf"):
            content = tf_file.read_text()
            assert "cookiecutter" not in content, (
                f"{tf_file} contains cookiecutter literal"
            )

    def test_cloudflare_origin_cert_present(self, project):
        content = (project / "terraform" / "cloudflare" / "main.tf").read_text()
        assert 'resource "tls_private_key" "origin"' in content
        assert 'resource "cloudflare_origin_ca_certificate" "origin"' in content
        assert '"hashicorp/tls"' in content

    def test_backup_cronjob_template_exists(self, project):
        assert (
            project / "helm" / "site" / "templates" / "postgres-backup-cronjob.yaml"
        ).exists()

    def test_backup_secret_template_exists(self, project):
        assert (project / "helm" / "site" / "templates" / "backup-secret.yaml").exists()

    def test_backup_disabled_by_default_in_values(self, project):
        content = (project / "helm" / "site" / "values.yaml").read_text()
        assert "backup:" in content
        assert "enabled: false" in content

    def test_backup_credentials_in_values(self, project):
        content = (project / "helm" / "site" / "values.yaml").read_text()
        assert "backupAccessKey" in content
        assert "backupSecretKey" in content
        assert "backupBucket" in content
        assert "backupEndpoint" in content

    def test_backup_docs_exist(self, project):
        assert (project / "docs" / "Database-Backups.md").exists()

    def test_i18n_and_storage_coexist(self, project):
        settings_content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" in settings_content
        assert "USE_I18N = True" in settings_content
        assert (project / "terraform" / "storage" / "main.tf").exists()
        assert (project / "locale").is_dir()


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
            "create-tag.md",
            "create-filter.md",
            "perf.md",
            "secure.md",
            "gdpr.md",
            "a11y.md",
            "deadcode.md",
            "full-coverage.md",
            "translate.md",
            "docs.md",
            "daisyui.md",
            "launch.md",
            "launch-observability.md",
            "rotate-secrets.md",
            "enable-db-backups.md",
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
            ["ruff", "check", "--no-cache", str(project)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"ruff check failed:\n{result.stdout}\n{result.stderr}"
        )
