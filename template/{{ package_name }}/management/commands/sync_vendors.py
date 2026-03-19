from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

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
        vendors_path = settings.BASE_DIR / VENDORS_FILE
        if not vendors_path.exists():
            raise CommandError(f"{VENDORS_FILE} not found at {vendors_path}.")

        all_vendors: dict[str, Any] = json.loads(vendors_path.read_text())
        if not all_vendors:
            raise CommandError(f"No vendors defined in {VENDORS_FILE}.")

        vendors = all_vendors
        if package:
            if package not in all_vendors:
                raise CommandError(
                    f"Unknown package '{package}'. Available: {', '.join(all_vendors)}"
                )
            vendors = {package: all_vendors[package]}

        updates = list(self._check_versions(vendors))

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
                self.style.WARNING("\nVendor updates may introduce breaking changes.")
            )
            confirm = input("Proceed with download? [y/N] ").strip().lower()
            if confirm != "y":
                self.stdout.write("Aborted.")
                return

        self._download_updates(updates, all_vendors, vendors_path)
        self.stdout.write(self.style.SUCCESS(f"\n{len(updates)} package(s) updated."))

    def _latest_github_version(
        self, source_url: str, repo: str | None = None
    ) -> str | None:
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

    def _download(self, url: str, dest: Path) -> None:
        """Download a file from a URL to a local path."""
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
            content = response.read()
        with dest.open("wb") as f:
            f.write(content)

    def _check_versions(
        self,
        vendors: dict[str, Any],
    ) -> Iterator[tuple[str, str]]:
        """Check each vendor for available updates. Yields (name, current, latest)."""
        for name, config in vendors.items():
            current = config["version"]
            source_url = config.get("source") or config["files"][0]["source"]
            repo = config.get("repo")
            try:
                latest = self._latest_github_version(source_url, repo=repo)
            except (
                json.JSONDecodeError,
                urllib.error.URLError,
                KeyError,
                TimeoutError,
            ) as exc:
                self.stdout.write(
                    self.style.WARNING(f"  {name}: failed to check ({exc})")
                )
                continue

            if not latest:
                self.stdout.write(
                    self.style.WARNING(f"  {name}: could not determine latest version")
                )
                continue

            if latest == current:
                self.stdout.write(f"  {name}: {current} (up to date)")
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"  {name}: {current} -> {latest}")
                )
                yield name, latest

    def _download_updates(
        self,
        updates: list[tuple[str, str]],
        all_vendors: dict[str, Any],
        vendors_path: Path,
    ) -> None:
        """Download updated files for each vendor and update vendors.json."""
        for name, latest in updates:
            config = all_vendors[name]
            files = config.get("files", [])
            if not files:
                files = [{"source": config["source"], "dest": config["dest"]}]

            for file_info in files:
                url = file_info["source"].format(version=latest)
                dest = settings.BASE_DIR / file_info["dest"]
                self.stdout.write(f"  Downloading {name}: {url}")
                try:
                    self._download(url, dest)
                except (urllib.error.URLError, OSError) as exc:
                    raise CommandError(f"Failed to download {name}: {exc}") from exc

            all_vendors[name]["version"] = latest
            self.stdout.write(self.style.SUCCESS(f"  {name} updated to {latest}"))

        vendors_path.write_text(json.dumps(all_vendors, indent=2) + "\n")
        self.stdout.write(self.style.SUCCESS(f"  Updated {vendors_path.name}"))
