"""Tests on the shared rendered project: structure, content, terraform, features, skills."""

from __future__ import annotations

import py_compile
import re
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
        assert (project / "docs" / "database-backups.md").exists()

    def test_single_node_topology_is_the_default(self, project):
        content = (
            project / "terraform" / "hetzner" / "terraform.tfvars.example"
        ).read_text()
        assert "create_database  = false" in content
        assert "create_jobrunner = false" in content
        assert "webapp_count     = 0" in content
        assert "create_monitor = false" in content

    def test_hetzner_topology_variables_exist(self, project):
        content = (project / "terraform" / "hetzner" / "variables.tf").read_text()
        for name in ("create_database", "create_jobrunner", "webapp_count"):
            assert f'variable "{name}"' in content

    def test_server_node_type_sized_for_single_node(self, project):
        content = (project / "terraform" / "hetzner" / "variables.tf").read_text()
        start = content.index('variable "server_type"')
        assert '"cx33"' in content[start : content.index("\n}", start)]

    def test_server_node_takes_unclaimed_workload_labels(self, project):
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert "server_workload_labels" in content
        assert 'var.webapp_count == 0 ? "webapp=true" : ""' in content
        assert 'var.create_jobrunner ? "" : "jobrunner=true"' in content
        assert 'var.create_database ? "" : "database=true"' in content

    def test_optional_nodes_are_conditional(self, project):
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert "count        = var.create_database ? 1 : 0" in content
        assert "count        = var.create_jobrunner ? 1 : 0" in content

    def test_postgres_volume_follows_the_database(self, project):
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert (
            "server_id = var.create_database "
            "? hcloud_server.database[0].id : hcloud_server.server.id"
        ) in content

    def test_tailscale_variables_exist_and_default_to_disabled(self, project):
        content = (project / "terraform" / "hetzner" / "variables.tf").read_text()
        for name in (
            "tailscale_oauth_client_secret",
            "tailscale_tailnet",
            "tailscale_tag",
        ):
            assert f'variable "{name}"' in content
        start = content.index('variable "tailscale_oauth_client_secret"')
        block = content[start : content.index("\n}", start)]
        assert 'default     = ""' in block, "Tailscale must be off by default"
        assert "sensitive   = true" in block

    def test_tailscale_enabled_is_not_marked_sensitive(self, project):
        """Sensitivity propagates from the OAuth secret; without nonsensitive()
        it taints the MagicDNS host that get-kubeconfig.sh must read."""
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert "nonsensitive(var.tailscale_oauth_client_secret" in content, (
            "tailscale_enabled must be unwrapped or the outputs fail to validate"
        )

    def test_tailscale_tailnet_required_when_enabled(self, project):
        content = (project / "terraform" / "hetzner" / "main.tf").read_text()
        assert "precondition" in content
        assert (
            'var.tailscale_oauth_client_secret == "" || var.tailscale_tailnet != ""'
            in content
        )

    def test_cloud_init_tailscale_block_is_conditional(self, project):
        templates = project / "terraform" / "hetzner" / "templates"
        for name in (
            "cloud_init_server.tftpl",
            "cloud_init_agent.tftpl",
            "cloud_init_database.tftpl",
        ):
            content = (templates / name).read_text()
            assert "%{ if tailscale_enabled ~}" in content, name
            assert "tailscale up" in content, name
            assert "--advertise-tags=${tailscale_tag}" in content, name
            # hostname is pinned rather than left to Tailscale normalisation,
            # because the server's TLS SAN is derived from it at install time
            assert "--hostname=${tailscale_hostname}" in content, name

    def test_server_cert_carries_the_tailnet_san(self, project):
        content = (
            project / "terraform" / "hetzner" / "templates" / "cloud_init_server.tftpl"
        ).read_text()
        assert '--tls-san="$PUBLIC_IP" ${tailscale_tls_san}' in content

    def test_cloud_init_emits_workload_labels(self, project):
        templates = project / "terraform" / "hetzner" / "templates"
        server = (templates / "cloud_init_server.tftpl").read_text()
        assert "--node-label=role=server ${workload_labels}" in server
        agent = (templates / "cloud_init_agent.tftpl").read_text()
        assert "--node-label=role=${role} ${workload_label}" in agent
        database = (templates / "cloud_init_database.tftpl").read_text()
        assert "--node-label=database=true" in database

    def test_workloads_select_boolean_labels_not_roles(self, project):
        """A node carries one role= but can carry all three booleans, so the
        chart is identical single-node and split."""
        expected = {
            "django-deployment.yaml": 'webapp: "true"',
            "django-worker-deployment.yaml": 'jobrunner: "true"',
            "cronjobs.yaml": 'jobrunner: "true"',
            "release-job.yaml": 'jobrunner: "true"',
            "postgres-backup-cronjob.yaml": 'jobrunner: "true"',
            "postgres-statefulset.yaml": 'database: "true"',
            "postgres-upgrade.yaml": 'database: "true"',
            "redis-deployment.yaml": 'database: "true"',
        }
        for name, selector in expected.items():
            content = (project / "helm" / "site" / "templates" / name).read_text()
            assert selector in content, name
            assert "role: " not in content, name

    def test_single_node_resource_requests_fit_one_cx33(self, project):
        """~2.6 GB requested of 8 GB, leaving room for k3s itself."""
        content = (project / "helm" / "site" / "values.yaml").read_text()
        assert "replicas: 1" in content
        for request in ("memory: 1024Mi", "memory: 768Mi", "memory: 64Mi"):
            assert request in content

    def test_tailscale_skill_is_installed(self, project):
        skill = project / ".agents" / "skills" / "dj-tailscale"
        assert (skill / "SKILL.md").exists()
        assert (skill / "references" / "help.md").exists()
        script = skill / "scripts" / "join-nodes.sh"
        assert script.exists()
        assert script.stat().st_mode & 0o111, "join-nodes.sh must be executable"

    def test_tailscale_skill_files_contain_no_jinja(self, project):
        """.agents/ is copied verbatim, so unrendered braces would ship as-is."""
        skill = project / ".agents" / "skills" / "dj-tailscale"
        for path in skill.rglob("*"):
            if path.is_file():
                content = path.read_text()
                assert "{{" not in content, path
                assert "{%" not in content, path

    def test_kubeconfig_prefers_the_tailnet_address(self, project):
        content = (project / "just" / "get-kubeconfig.sh").read_text()
        assert "server_tailscale_host" in content
        assert 'API_HOST="${TAILSCALE_HOST:-$SERVER_IP}"' in content

    def test_deploy_workflow_joins_tailnet_conditionally(self, project):
        content = (project / ".github" / "workflows" / "deploy.yml").read_text()
        assert "tailscale/github-action@" in content
        assert "if: ${{ secrets.TS_OAUTH_CLIENT_ID != '' }}" in content
        # the runner must be on the tailnet before helm tries to reach the API
        assert content.index("Connect to Tailscale") < content.index(
            "Deploy to Kubernetes"
        )

    def test_tailscale_documented_in_all_command_tables(self, project):
        """AGENTS.md requires the skill tables stay in lockstep."""
        for rel in ("AGENTS.md", "README.md"):
            assert "/dj-tailscale" in (project / rel).read_text(), rel

    def test_i18n_and_storage_coexist(self, project):
        settings_content = (project / "config" / "settings.py").read_text()
        assert "S3Boto3Storage" in settings_content
        assert "USE_I18N = True" in settings_content
        assert (project / "terraform" / "storage" / "main.tf").exists()
        assert (project / "locale").is_dir()


class TestReferenceIntegrity:
    """Docs and skills must point at files and value keys that actually exist."""

    @staticmethod
    def _text_files(project):
        for pattern in ("*.md", "*.sh"):
            for path in project.rglob(pattern):
                if ".git" not in path.parts and ".venv" not in path.parts:
                    yield path

    def test_no_references_to_the_old_bin_script_directory(self, project):
        """Skill scripts live in scripts/; bin/ is a leftover from the rename."""
        stale = [
            f"{path.relative_to(project)}:{i}"
            for path in self._text_files(project)
            for i, line in enumerate(path.read_text().splitlines(), 1)
            if re.search(r"skills/[\w-]+/bin/", line)
        ]
        assert not stale, "references to skills/<name>/bin/: " + ", ".join(stale)

    def test_every_referenced_skill_script_exists(self, project):
        missing = []
        for path in self._text_files(project):
            for ref in re.findall(
                r"\.agents/skills/[\w./-]+\.(?:sh|py)", path.read_text()
            ):
                if not (project / ref).exists():
                    missing.append(f"{path.relative_to(project)} -> {ref}")
        assert not missing, "referenced scripts do not exist: " + ", ".join(missing)

    def test_object_storage_keys_match_the_chart(self, project):
        """templates/secret.yaml reads secrets.objectStorage*, so that is the
        canonical name - values.yaml must declare the same keys."""
        secret_tmpl = (
            project / "helm" / "site" / "templates" / "secret.yaml"
        ).read_text()
        values = (project / "helm" / "site" / "values.yaml").read_text()
        consumed = set(
            re.findall(r"\.Values\.secrets\.(objectStorage\w+)", secret_tmpl)
        )
        assert consumed, "expected secret.yaml to read objectStorage* keys"
        for key in sorted(consumed):
            assert f"{key}:" in values, f"values.yaml does not declare {key}"

    def test_secret_values_example_holds_only_secrets(self, project):
        """values.secret.yaml is gitignored; anything non-secret belongs in
        values.yaml so it can be committed and tested."""
        content = (project / "helm" / "site" / "values.secret.yaml.example").read_text()
        top_level = {
            line.split(":")[0]
            for line in content.splitlines()
            if line and not line.startswith((" ", "#"))
        }
        assert top_level == {"secrets"}, f"non-secret top-level keys: {top_level}"

    def test_non_secret_config_defaults_come_from_copier_answers(self, project):
        values = (project / "helm" / "site" / "values.yaml").read_text()
        for key, expected in (
            ("domain", "example.com"),
            ("allowedHosts", ".example.com"),
            ("admins", "test@example.com"),
            ("contactEmail", "test@example.com"),
            ("mailgunSenderDomain", "example.com"),
            ("metaAuthor", "Test Author"),
            ("metaDescription", "A test project"),
        ):
            assert f'{key}: "{expected}"' in values, (
                f"{key} not defaulted in values.yaml"
            )

    def test_non_secret_config_is_not_in_the_secret_file(self, project):
        content = (project / "helm" / "site" / "values.secret.yaml.example").read_text()
        for key in (
            "domain:",
            "image:",
            "replicas:",
            "volumePath:",
            "adminUrl:",
            "admins:",
            "allowedHosts:",
            "contactEmail:",
            "metaAuthor:",
            "metaDescription:",
            "mailgunSenderDomain:",
            "secureSslRedirect:",
        ):
            assert key not in content, f"{key} should have moved to values.yaml"

    def test_no_references_to_the_wrong_object_storage_prefix(self, project):
        stale = [
            f"{path.relative_to(project)}:{i}"
            for path in self._text_files(project)
            for i, line in enumerate(path.read_text().splitlines(), 1)
            if "hetznerStorage" in line
        ]
        values = project / "helm" / "site" / "values.yaml"
        if "hetznerStorage" in values.read_text():
            stale.append(str(values.relative_to(project)))
        assert not stale, "stale hetznerStorage* references: " + ", ".join(stale)


class TestClaudeHooksInstallation:
    """Verify that .claude/ hooks are written by the post-gen hook."""

    def test_settings_json_installed(self, project):
        assert (project / ".claude" / "settings.json").exists()

    def test_command_stubs_installed(self, project):
        # Every skill with a SKILL.md should have a corresponding stub
        skills = list((project / ".agents" / "skills").glob("*/SKILL.md"))
        assert skills, "No SKILL.md files found in .agents/skills/"
        commands_dir = project / ".claude" / "commands"
        for skill_md in skills:
            name = skill_md.parent.name  # e.g. "dj-create-app"
            stub = commands_dir / f"{name}.md"
            assert stub.exists(), f"Missing stub for skill '{name}'"
            assert stub.read_text().strip() == f"@.agents/skills/{name}/SKILL.md"


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
