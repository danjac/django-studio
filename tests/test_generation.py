"""Tests for template generation behaviour: slug derivation, domain, license."""

from __future__ import annotations

import datetime
import tempfile
from pathlib import Path

import pytest

from tests.helpers import DEFAULT_CONTEXT, render


def test_template_renders_without_error(output_dir):
    result = render(output_dir, DEFAULT_CONTEXT)
    assert result.exists()


class TestProjectNameDerivation:
    """Test that project_slug and package_name are derived from project_name."""

    def test_slug_derived_from_project_name(self, output_dir):
        project = render(
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
        project = render(
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
            render(
                output_dir,
                {
                    "project_name": "",
                    "description": "A test",
                    "author": "Author",
                    "author_email": "author@example.com",
                },
            )


class TestDomainPrefill:
    """Test that the domain variable is substituted into config files."""

    def test_cloudflare_tfvars_has_domain(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "domain": "myapp.example.org"})
        content = (
            project / "terraform" / "cloudflare" / "terraform.tfvars.example"
        ).read_text()
        assert 'domain = "myapp.example.org"' in content

    def test_cloudflare_tfvars_default_domain(self, output_dir):
        project = render(output_dir, DEFAULT_CONTEXT)
        content = (
            project / "terraform" / "cloudflare" / "terraform.tfvars.example"
        ).read_text()
        assert 'domain = "example.com"' in content

    def test_helm_site_values_has_domain(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "domain": "myapp.example.org"})
        content = (project / "helm" / "site" / "values.secret.yaml.example").read_text()
        assert 'domain: "myapp.example.org"' in content
        assert 'allowedHosts: ".myapp.example.org"' in content

    def test_helm_site_values_no_change_me_for_domain(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "domain": "myapp.example.org"})
        content = (project / "helm" / "site" / "values.secret.yaml.example").read_text()
        lines = {line.strip() for line in content.splitlines()}
        assert not any(
            "CHANGE_ME" in line
            for line in lines
            if "domain" in line or "allowedHosts" in line
        )

    def test_helm_observability_grafana_host_has_domain(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "domain": "myapp.example.org"})
        content = (
            project / "helm" / "observability" / "values.secret.yaml.example"
        ).read_text()
        assert "grafana.myapp.example.org" in content

    def test_no_cookiecutter_literals_in_domain_fields(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "domain": "myapp.example.org"})
        content = (project / "helm" / "site" / "values.secret.yaml.example").read_text()
        assert "cookiecutter" not in content
        content = (
            project / "terraform" / "cloudflare" / "terraform.tfvars.example"
        ).read_text()
        assert "cookiecutter" not in content


class TestLicensePrompt:
    """Test license prompt behaviour."""

    def test_mit_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "MIT"})
        assert (project / "LICENSE").exists()

    def test_mit_license_content(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "MIT"})
        content = (project / "LICENSE").read_text()
        assert "MIT License" in content
        assert DEFAULT_CONTEXT["author"] in content

    def test_gpl_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "GPL-3.0"})
        content = (project / "LICENSE").read_text()
        assert "GNU General Public License" in content

    def test_agpl_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "AGPL-3.0"})
        content = (project / "LICENSE").read_text()
        assert "GNU Affero General Public License" in content

    def test_apache_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "Apache-2.0"})
        content = (project / "LICENSE").read_text()
        assert "Apache License" in content

    def test_lgpl_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "LGPL-3.0"})
        content = (project / "LICENSE").read_text()
        assert "GNU Lesser General Public License" in content

    def test_mpl_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "MPL-2.0"})
        content = (project / "LICENSE").read_text()
        assert "Mozilla Public License" in content

    def test_bsd2_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "BSD-2-Clause"})
        content = (project / "LICENSE").read_text()
        assert "BSD 2-Clause" in content

    def test_bsd3_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "BSD-3-Clause"})
        content = (project / "LICENSE").read_text()
        assert "BSD 3-Clause" in content

    def test_isc_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "ISC"})
        content = (project / "LICENSE").read_text()
        assert "ISC License" in content

    def test_eupl_license_file_created(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "EUPL-1.2"})
        content = (project / "LICENSE").read_text()
        assert "European Union Public Licence" in content

    def test_none_license_skips_file(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "None"})
        assert not (project / "LICENSE").exists()

    def test_pyproject_license_set_when_chosen(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "MIT"})
        content = (project / "pyproject.toml").read_text()
        assert 'license = { text = "MIT" }' in content

    def test_pyproject_license_absent_when_none(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "None"})
        content = (project / "pyproject.toml").read_text()
        assert "license" not in content

    def test_license_year_substituted(self, output_dir):
        project = render(output_dir, {**DEFAULT_CONTEXT, "license": "MIT"})
        content = (project / "LICENSE").read_text()
        assert str(datetime.date.today().year) in content


class TestPostGenBackup:
    """Test that the hook backs up generated files before overwriting on re-render."""

    def test_settings_json_backed_up_on_re_render(self, output_dir):
        project = render(output_dir, DEFAULT_CONTEXT)
        original = (project / ".claude" / "settings.json").read_text()
        bak = Path(tempfile.gettempdir()) / "test_project" / "settings.json.bak"
        bak.unlink(missing_ok=True)

        render(output_dir, DEFAULT_CONTEXT)

        assert bak.exists()
        assert bak.read_text() == original

    def test_mcp_json_backed_up_on_re_render(self, output_dir):
        project = render(output_dir, DEFAULT_CONTEXT)
        original = (project / ".mcp.json").read_text()
        bak = Path(tempfile.gettempdir()) / "test_project" / "mcp.json.bak"
        bak.unlink(missing_ok=True)

        render(output_dir, DEFAULT_CONTEXT)

        assert bak.exists()
        assert bak.read_text() == original

    def test_opencode_json_backed_up_on_re_render(self, output_dir):
        project = render(output_dir, DEFAULT_CONTEXT)
        original = (project / "opencode.json").read_text()
        bak = Path(tempfile.gettempdir()) / "test_project" / "opencode.json.bak"
        bak.unlink(missing_ok=True)

        render(output_dir, DEFAULT_CONTEXT)

        assert bak.exists()
        assert bak.read_text() == original

    def test_no_backup_if_file_absent(self, output_dir):
        bak = Path(tempfile.gettempdir()) / "test_project" / "settings.json.bak"
        bak.unlink(missing_ok=True)
        # Render into a fresh directory — settings.json doesn't exist yet
        project = render(output_dir, DEFAULT_CONTEXT)
        assert (project / ".claude" / "settings.json").exists()
        # The hook should not have created a backup (nothing to back up)
        assert not bak.exists()
