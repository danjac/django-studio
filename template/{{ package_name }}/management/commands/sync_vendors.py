from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

if TYPE_CHECKING:
    from django.core.management.base import OutputWrapper

VENDORS_FILE = "vendors.json"


class Command(BaseCommand):
    """Check and update vendored frontend dependencies."""

    help = "Update vendored frontend dependencies defined in vendors.json."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add optional package name argument."""
        parser.add_argument(
            "package",
            nargs="?",
            help="Update a single package (default: all)",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Check for updates without downloading",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            dest="no_input",
            help="Skip confirmation prompt",
        )

    def handle(
        self, *, package: str | None, check: bool, no_input: bool, **options: Any
    ) -> None:
        """Check for and download vendor updates."""
        vendors_path = Path(settings.BASE_DIR) / VENDORS_FILE
        if not vendors_path.exists():
            raise CommandError(f"{VENDORS_FILE} not found at {vendors_path}.")

        vendors: dict[str, Any] = json.loads(vendors_path.read_text())
        if not vendors:
            raise CommandError(f"No vendors defined in {VENDORS_FILE}.")

        if package:
            if package not in vendors:
                raise CommandError(
                    f"Unknown package '{package}'. Available: {', '.join(vendors)}"
                )
            vendors = {package: vendors[package]}

        updates = _check_versions(vendors, self.stdout, self.style)

        if not updates:
            self.stdout.write(self.style.SUCCESS("\nAll vendors up to date."))
            return

        if check:
            self.stdout.write(
                f"\n{len(updates)} update(s) available. "
                "Run without --check to download."
            )
            return

        if not no_input:
            self.stdout.write(
                self.style.WARNING(
                    "\nVendor updates may introduce breaking changes."
                )
            )
            confirm = input("Proceed with download? [y/N] ").strip().lower()
            if confirm != "y":
                self.stdout.write("Aborted.")
                return

        _download_updates(updates, Path(settings.BASE_DIR), vendors_path, self.stdout, self.style)
        self.stdout.write(self.style.SUCCESS(f"\n{len(updates)} package(s) updated."))


def _latest_github_version(source_url: str, repo: str | None = None) -> str | None:
    """Query GitHub for the latest release version of a repo."""
    if not repo:
        match = re.match(r"https://github\.com/([^/]+/[^/]+)/", source_url)
        if not match:
            return None
        repo = match.group(1)
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    request = urllib.request.Request(  # noqa: S310
        api_url,
        headers={"Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
        data = json.loads(response.read())
    return data["tag_name"].lstrip("v")


def _download(url: str, dest: Path) -> None:
    """Download a file from a URL to a local path."""
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
        content = response.read()
    with dest.open("wb") as f:
        f.write(content)


def _check_versions(
    vendors: dict[str, Any],
    stdout: OutputWrapper,
    style: Any,
) -> list[tuple[str, str, str]]:
    """Check each vendor for available updates. Returns list of (name, current, latest)."""
    updates: list[tuple[str, str, str]] = []
    for name, config in vendors.items():
        current = config["version"]
        source_url = config.get("source") or config["files"][0]["source"]
        repo = config.get("repo")
        try:
            latest = _latest_github_version(source_url, repo=repo)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            stdout.write(style.WARNING(f"  {name}: failed to check ({exc})"))
            continue

        if not latest:
            stdout.write(style.WARNING(f"  {name}: could not determine latest version"))
            continue

        if latest == current:
            stdout.write(f"  {name}: {current} (up to date)")
        else:
            updates.append((name, current, latest))
            stdout.write(style.SUCCESS(f"  {name}: {current} -> {latest}"))

    return updates


def _download_updates(
    updates: list[tuple[str, str, str]],
    base_dir: Path,
    vendors_path: Path,
    stdout: OutputWrapper,
    style: Any,
) -> None:
    """Download updated files for each vendor and update vendors.json."""
    all_vendors: dict[str, Any] = json.loads(vendors_path.read_text())

    for name, _current, latest in updates:
        config = all_vendors[name]
        files = config.get("files", [])
        if not files:
            files = [{"source": config["source"], "dest": config["dest"]}]

        for file_info in files:
            url = file_info["source"].format(version=latest)
            dest = base_dir / file_info["dest"]
            stdout.write(f"  Downloading {name}: {url}")
            try:
                _download(url, dest)
            except (urllib.error.URLError, OSError) as exc:
                raise CommandError(f"Failed to download {name}: {exc}") from exc

        all_vendors[name]["version"] = latest
        stdout.write(style.SUCCESS(f"  {name} updated to {latest}"))

    vendors_path.write_text(json.dumps(all_vendors, indent=2) + "\n")
    stdout.write(style.SUCCESS(f"  Updated {vendors_path.name}"))
