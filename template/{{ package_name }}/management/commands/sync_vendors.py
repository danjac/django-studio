from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict

if TYPE_CHECKING:
    from pathlib import Path

import aiohttp
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser


class VendorFile(TypedDict):
    """A single file entry within a vendor package."""

    source: str
    dest: str


class VendorConfig(TypedDict):
    """Configuration for a vendored frontend package."""

    version: str
    source: NotRequired[str]
    dest: NotRequired[str]
    files: NotRequired[list[VendorFile]]
    repo: NotRequired[str]


class Command(BaseCommand):
    """Check and update vendored frontend dependencies."""

    help = "Update vendored frontend dependencies defined in vendors.json."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command arguments."""
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
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="HTTP request timeout in seconds (default: 30)",
        )

    def handle(
        self, *, check: bool, no_input: bool, timeout: int, **options: Any
    ) -> None:
        """Check for and download vendor updates."""
        vendors = self._load_vendors()

        try:
            asyncio.run(
                self._handle(
                    vendors=vendors,
                    check=check,
                    no_input=no_input,
                    timeout=timeout,
                )
            )
        except KeyError as exc:
            raise CommandError(
                f"Malformed vendors config in {settings.VENDORS_FILE}: missing key {exc}"
            ) from exc

    def _load_vendors(self) -> dict[str, VendorConfig]:
        """Load and return vendors.json contents.

        Raises CommandError if the file is missing or invalid.
        """
        if not settings.VENDORS_FILE.exists():
            raise CommandError(f"{settings.VENDORS_FILE} not found.")

        try:
            vendors: dict[str, VendorConfig] = json.loads(
                settings.VENDORS_FILE.read_text()
            )
        except json.JSONDecodeError as exc:
            raise CommandError(
                f"{settings.VENDORS_FILE} is not valid JSON: {exc}"
            ) from exc

        if not vendors:
            raise CommandError(f"No vendors defined in {settings.VENDORS_FILE}.")

        return vendors

    async def _handle(
        self,
        *,
        vendors: dict[str, VendorConfig],
        check: bool,
        no_input: bool,
        timeout: int,
    ) -> None:
        async with aiohttp.ClientSession() as session:
            updates = await self._check_versions(session, vendors, timeout=timeout)

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
            await self._download_updates(session, updates=updates, vendors=vendors, timeout=timeout)
        self.stdout.write(self.style.SUCCESS(f"\n{len(updates)} package(s) updated."))

    async def _latest_github_version(
        self,
        session: aiohttp.ClientSession,
        *,
        source_url: str,
        repo: str | None = None,
        timeout: int,
    ) -> str | None:
        """Query GitHub for the latest release version of a repo."""
        if not repo:
            match = re.match(r"https://github\.com/([^/]+/[^/]+)/", source_url)
            if not match:
                return None
            repo = match.group(1)
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        async with session.get(
            api_url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            data = await response.json()
        return data["tag_name"].lstrip("v")

    async def _check_version(
        self,
        session: aiohttp.ClientSession,
        config: VendorConfig,
        *,
        name: str,
        timeout: int,
    ) -> tuple[str, str] | None:
        """Check a single vendor for updates. Returns (name, latest) or None."""
        current = config["version"]
        source_url = config.get("source") or (config.get("files") or [])[0]["source"]
        repo = config.get("repo")
        try:
            latest = await self._latest_github_version(
                session,
                source_url=source_url,
                repo=repo,
                timeout=timeout,
            )
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
        vendors: dict[str, VendorConfig],
        timeout: int = 30,
    ) -> list[tuple[str, str]]:
        """Check all vendors in parallel. Returns list of (name, latest)."""
        results = await asyncio.gather(
            *[
                self._check_version(session, config, name=name, timeout=timeout)
                for name, config in vendors.items()
            ]
        )
        return [r for r in results if r is not None]

    async def _download_file(
        self,
        session: aiohttp.ClientSession,
        *,
        name: str,
        url: str,
        timeout: int,
        dest: Path,
    ) -> None:
        """Download a single vendor file."""
        self.stdout.write(f"  Downloading {name}: {url}")
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                content = await response.read()
            dest.write_bytes(content)
        except (aiohttp.ClientError, OSError) as exc:
            raise CommandError(f"Failed to download {name}: {exc}") from exc

    async def _download_updates(
        self,
        session: aiohttp.ClientSession,
        *,
        updates: list[tuple[str, str]],
        vendors: dict[str, VendorConfig],
        timeout: int = 30,
    ) -> None:
        """Download all updated vendor files in parallel, then update vendors.json."""
        tasks = []
        for name, latest in updates:
            config = vendors[name]
            files = config.get("files", [])
            if not files:
                files = [
                    {
                        "source": config.get("source", ""),
                        "dest": config.get("dest", ""),
                    }
                ]
            for file_info in files:
                url = file_info["source"].format(version=latest)
                dest = settings.VENDORS_FILE.parent / file_info["dest"]
                tasks.append(
                    self._download_file(
                        session,
                        name=name,
                        url=url,
                        dest=dest,
                        timeout=timeout,
                    )
                )

        await asyncio.gather(*tasks)

        for name, latest in updates:
            vendors[name]["version"] = latest
            self.stdout.write(self.style.SUCCESS(f"  {name} updated to {latest}"))

        settings.VENDORS_FILE.write_text(json.dumps(vendors, indent=2) + "\n")
        self.stdout.write(self.style.SUCCESS(f"  Updated {settings.VENDORS_FILE.name}"))
