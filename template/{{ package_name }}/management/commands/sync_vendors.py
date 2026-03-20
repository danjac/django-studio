from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import aiohttp
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser


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
        asyncio.run(self._handle(package=package, check=check, no_input=no_input))

    async def _handle(
        self, *, package: str | None, check: bool, no_input: bool
    ) -> None:
        if not settings.VENDORS_FILE.exists():
            raise CommandError(f"{settings.VENDORS_FILE} not found.")

        all_vendors: dict[str, Any] = json.loads(settings.VENDORS_FILE.read_text())
        if not all_vendors:
            raise CommandError(f"No vendors defined in {settings.VENDORS_FILE}.")

        vendors = all_vendors
        if package:
            if package not in all_vendors:
                raise CommandError(
                    f"Unknown package '{package}'. Available: {', '.join(all_vendors)}"
                )
            vendors = {package: all_vendors[package]}

        async with aiohttp.ClientSession() as session:
            updates = await self._check_versions(session, vendors)

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

        async with aiohttp.ClientSession() as session:
            await self._download_updates(session, updates, all_vendors)
        self.stdout.write(self.style.SUCCESS(f"\n{len(updates)} package(s) updated."))

    async def _latest_github_version(
        self,
        session: aiohttp.ClientSession,
        source_url: str,
        repo: str | None = None,
    ) -> str | None:
        """Query GitHub for the latest release version of a repo."""
        if not repo:
            match = re.match(r"https://github\.com/([^/]+/[^/]+)/", source_url)
            if not match:
                return None
            repo = match.group(1)
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        timeout = aiohttp.ClientTimeout(total=15)
        async with session.get(
            api_url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=timeout,
        ) as response:
            data = await response.json()
        return data["tag_name"].lstrip("v")

    async def _check_version(
        self,
        session: aiohttp.ClientSession,
        name: str,
        config: dict[str, Any],
    ) -> tuple[str, str] | None:
        """Check a single vendor for updates. Returns (name, latest) or None."""
        current = config["version"]
        source_url = config.get("source") or config["files"][0]["source"]
        repo = config.get("repo")
        try:
            latest = await self._latest_github_version(session, source_url, repo=repo)
        except (
            aiohttp.ClientError,
            TimeoutError,
            json.JSONDecodeError,
            KeyError,
        ) as exc:
            self.stdout.write(self.style.WARNING(f"  {name}: failed to check ({exc})"))
            return None

        if not latest:
            self.stdout.write(
                self.style.WARNING(f"  {name}: could not determine latest version")
            )
            return None

        if latest == current:
            self.stdout.write(f"  {name}: {current} (up to date)")
        else:
            self.stdout.write(self.style.SUCCESS(f"  {name}: {current} -> {latest}"))
            return name, latest
        return None

    async def _check_versions(
        self,
        session: aiohttp.ClientSession,
        vendors: dict[str, Any],
    ) -> list[tuple[str, str]]:
        """Check all vendors in parallel. Returns list of (name, latest)."""
        results = await asyncio.gather(
            *[
                self._check_version(session, name, config)
                for name, config in vendors.items()
            ]
        )
        return [r for r in results if r is not None]

    async def _download_file(
        self,
        session: aiohttp.ClientSession,
        name: str,
        url: str,
        dest: Path,
    ) -> None:
        """Download a single vendor file."""
        self.stdout.write(f"  Downloading {name}: {url}")
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.get(url, timeout=timeout) as response:
                content = await response.read()
            dest.write_bytes(content)
        except (aiohttp.ClientError, OSError) as exc:
            raise CommandError(f"Failed to download {name}: {exc}") from exc

    async def _download_updates(
        self,
        session: aiohttp.ClientSession,
        updates: list[tuple[str, str]],
        all_vendors: dict[str, Any],
    ) -> None:
        """Download all updated vendor files in parallel, then update vendors.json."""
        tasks = []
        for name, latest in updates:
            config = all_vendors[name]
            files = config.get("files", [])
            if not files:
                files = [{"source": config["source"], "dest": config["dest"]}]
            for file_info in files:
                url = file_info["source"].format(version=latest)
                dest = settings.VENDORS_FILE.parent / file_info["dest"]
                tasks.append(self._download_file(session, name, url, dest))

        await asyncio.gather(*tasks)

        for name, latest in updates:
            all_vendors[name]["version"] = latest
            self.stdout.write(self.style.SUCCESS(f"  {name} updated to {latest}"))

        settings.VENDORS_FILE.write_text(json.dumps(all_vendors, indent=2) + "\n")
        self.stdout.write(self.style.SUCCESS(f"  Updated {settings.VENDORS_FILE.name}"))
