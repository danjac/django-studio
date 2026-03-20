from __future__ import annotations

import json
import re
from io import StringIO
from unittest.mock import patch

import aiohttp
import pytest
from aioresponses import aioresponses
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import CommandError

GITHUB_API_RE = re.compile(r"https://api\.github\.com/repos/.+/releases/latest")
CDN_RE = re.compile(r"https://cdn\.jsdelivr\.net/.+")
GITHUB_RELEASE_RE = re.compile(r"https://github\.com/.+/releases/download/.+")


# ---------------------------------------------------------------------------
# set_default_site
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSetDefaultSite:
    def test_sets_domain_and_name(self):
        call_command("set_default_site", "example.com", "My App")
        site = Site.objects.get_current()
        assert site.domain == "example.com"
        assert site.name == "My App"

    def test_outputs_success_message(self):
        out = StringIO()
        call_command("set_default_site", "example.com", "My App", stdout=out)
        assert "example.com" in out.getvalue()


# ---------------------------------------------------------------------------
# sync_vendors fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vendors_dir(tmp_path, settings):
    settings.VENDORS_FILE = tmp_path / "vendors.json"
    vendors = {
        "htmx": {
            "version": "2.0.7",
            "repo": "bigskysoftware/htmx",
            "source": "https://cdn.jsdelivr.net/npm/htmx.org@{version}/dist/htmx.min.js",
            "dest": "static/vendor/htmx.js",
        },
    }
    (tmp_path / "vendors.json").write_text(json.dumps(vendors))
    dest = tmp_path / "static" / "vendor"
    dest.mkdir(parents=True)
    (dest / "htmx.js").write_bytes(b"old-content")
    return tmp_path


# ---------------------------------------------------------------------------
# sync_vendors
# ---------------------------------------------------------------------------


class TestSyncVendors:
    def test_missing_vendors_file(self, tmp_path, settings):
        settings.VENDORS_FILE = tmp_path / "vendors.json"
        with pytest.raises(CommandError, match="not found"):
            call_command("sync_vendors")

    def test_empty_vendors_file(self, tmp_path, settings):
        settings.VENDORS_FILE = tmp_path / "vendors.json"
        (tmp_path / "vendors.json").write_text("{}")
        with pytest.raises(CommandError, match="No vendors defined"):
            call_command("sync_vendors")

    def test_unknown_package(self, vendors_dir):
        with pytest.raises(CommandError, match="Unknown package"):
            call_command("sync_vendors", "nonexistent")

    def test_all_up_to_date(self, vendors_dir):
        out = StringIO()
        with aioresponses() as m:
            m.get(GITHUB_API_RE, payload={"tag_name": "v2.0.7"})
            call_command("sync_vendors", stdout=out)
        assert "up to date" in out.getvalue()

    def test_check_flag_reports_updates_without_downloading(self, vendors_dir):
        out = StringIO()
        with aioresponses() as m:
            m.get(GITHUB_API_RE, payload={"tag_name": "v2.0.8"})
            call_command("sync_vendors", "--check", stdout=out)
        assert "1 update(s) available" in out.getvalue()
        vendors = json.loads((vendors_dir / "vendors.json").read_text())
        assert vendors["htmx"]["version"] == "2.0.7"

    def test_no_input_downloads_and_updates_json(self, vendors_dir):
        out = StringIO()
        with aioresponses() as m:
            m.get(GITHUB_API_RE, payload={"tag_name": "v2.0.8"})
            m.get(CDN_RE, body=b"new-content")
            call_command("sync_vendors", no_input=True, stdout=out)
        vendors = json.loads((vendors_dir / "vendors.json").read_text())
        assert vendors["htmx"]["version"] == "2.0.8"
        assert (vendors_dir / "static" / "vendor" / "htmx.js").read_bytes() == b"new-content"

    def test_confirmation_yes_downloads(self, vendors_dir):
        with aioresponses() as m:
            m.get(GITHUB_API_RE, payload={"tag_name": "v2.0.8"})
            m.get(CDN_RE, body=b"new-content")
            with patch("builtins.input", return_value="y"):
                call_command("sync_vendors")
        vendors = json.loads((vendors_dir / "vendors.json").read_text())
        assert vendors["htmx"]["version"] == "2.0.8"

    def test_confirmation_no_aborts(self, vendors_dir):
        out = StringIO()
        with aioresponses() as m:
            m.get(GITHUB_API_RE, payload={"tag_name": "v2.0.8"})
            with patch("builtins.input", return_value="n"):
                call_command("sync_vendors", stdout=out)
        assert "Aborted" in out.getvalue()
        vendors = json.loads((vendors_dir / "vendors.json").read_text())
        assert vendors["htmx"]["version"] == "2.0.7"

    def test_single_package_skips_others(self, tmp_path, settings):
        settings.VENDORS_FILE = tmp_path / "vendors.json"
        vendors = {
            "htmx": {
                "version": "2.0.7",
                "repo": "bigskysoftware/htmx",
                "source": "https://cdn.jsdelivr.net/npm/htmx.org@{version}/dist/htmx.min.js",
                "dest": "static/vendor/htmx.js",
            },
            "alpinejs": {
                "version": "3.15.2",
                "repo": "alpinejs/alpine",
                "source": "https://cdn.jsdelivr.net/npm/alpinejs@{version}/dist/cdn.min.js",
                "dest": "static/vendor/alpine.js",
            },
        }
        (tmp_path / "vendors.json").write_text(json.dumps(vendors))
        (tmp_path / "static" / "vendor").mkdir(parents=True)
        (tmp_path / "static" / "vendor" / "htmx.js").write_bytes(b"old")
        (tmp_path / "static" / "vendor" / "alpine.js").write_bytes(b"old")

        with aioresponses() as m:
            m.get(GITHUB_API_RE, payload={"tag_name": "v2.0.8"})
            m.get(CDN_RE, body=b"new-content")
            call_command("sync_vendors", "htmx", no_input=True)

        updated = json.loads((tmp_path / "vendors.json").read_text())
        assert updated["htmx"]["version"] == "2.0.8"
        assert updated["alpinejs"]["version"] == "3.15.2"

    def test_version_check_error_warns_and_continues(self, vendors_dir):
        out = StringIO()
        with aioresponses() as m:
            m.get(GITHUB_API_RE, exception=aiohttp.ClientConnectionError("network error"))
            call_command("sync_vendors", stdout=out)
        assert "failed to check" in out.getvalue()
