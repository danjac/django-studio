import asyncio
import json
import re
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict

import aiohttp
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from packaging.version import InvalidVersion, Version

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


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


GITHUB_REPO_RE = re.compile(r"https://github\.com/([^/]+/[^/]+)/")
GITHUB_API_HEADERS = {"Accept": "application/vnd.github+json"}


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
                self._run(
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

    # ------------------------------------------------------------------ I/O

    def _load_vendors(self) -> dict[str, VendorConfig]:
        """Load and return vendors.json contents."""
        path = settings.VENDORS_FILE
        if not path.exists():
            raise CommandError(f"{path} not found.")
        try:
            vendors: dict[str, VendorConfig] = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise CommandError(f"{path} is not valid JSON: {exc}") from exc
        if not vendors:
            raise CommandError(f"No vendors defined in {path}.")
        return vendors

    def _save_vendors(self, vendors: dict[str, VendorConfig]) -> None:
        settings.VENDORS_FILE.write_text(json.dumps(vendors, indent=2) + "\n")

    # --------------------------------------------------------------- logging

    def _warn(self, message: str) -> None:
        self.stdout.write(self.style.WARNING(f"  {message}"))

    def _info(self, message: str) -> None:
        self.stdout.write(f"  {message}")

    def _success(self, message: str) -> None:
        self.stdout.write(self.style.SUCCESS(f"  {message}"))

    # -------------------------------------------------------------- top-level

    async def _run(
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

        if not no_input and not self._confirm():
            return

        async with aiohttp.ClientSession() as session:
            await self._download_updates(
                session, updates=updates, vendors=vendors, timeout=timeout
            )
        self.stdout.write(self.style.SUCCESS(f"\n{len(updates)} package(s) updated."))

    def _confirm(self) -> bool:
        self.stdout.write(
            self.style.WARNING("\nVendor updates may introduce breaking changes.")
        )
        if input("Proceed with download? [y/N] ").strip().lower() == "y":
            return True
        self.stdout.write("Aborted.")
        return False

    # -------------------------------------------------------- GitHub lookups

    async def _fetch_first_tag(
        self,
        session: aiohttp.ClientSession,
        *,
        repo: str,
        timeout: int,
    ) -> str | None:
        """Fallback when /releases/latest 404s: take the first /tags entry."""
        url = f"https://api.github.com/repos/{repo}/tags"
        async with session.get(
            url,
            headers=GITHUB_API_HEADERS,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            if response.status != HTTPStatus.OK:
                return None
            tags = await response.json()
            return tags[0]["name"].lstrip("v") if tags else None

    async def _latest_github_version(
        self,
        session: aiohttp.ClientSession,
        *,
        config: VendorConfig,
        timeout: int,
    ) -> str | None:
        """Resolve the latest upstream version for `config`, if any."""
        repo = _resolve_repo(config)
        if not repo:
            return None
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        async with session.get(
            url,
            headers=GITHUB_API_HEADERS,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            if response.status == HTTPStatus.OK:
                data = await response.json()
                return data["tag_name"].lstrip("v")
            if response.status == HTTPStatus.NOT_FOUND:
                return await self._fetch_first_tag(session, repo=repo, timeout=timeout)
            error_body = await response.json()
            error_message = error_body.get("message", str(response.status))
            self._warn(f"/releases/latest returned {response.status}: {error_message}")
            return None

    # ----------------------------------------------------------- version check

    def _classify_update(
        self, name: str, current: str, latest: str
    ) -> tuple[str, str] | None:
        """Compare versions; return `(name, latest)` only if `latest > current`."""
        try:
            current_version = Version(current)
            latest_version = Version(latest)
        except InvalidVersion:
            self._warn(f"{name}: cannot compare versions ({current!r} vs {latest!r})")
            return None
        if latest_version < current_version:
            self._warn(
                f"{name}: {current} (upstream reports older {latest} — ignoring)"
            )
            return None
        if latest_version == current_version:
            self._info(f"{name}: {current} (up to date)")
            return None
        self._success(f"{name}: {current} -> {latest}")
        return name, latest

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
        try:
            latest = await self._latest_github_version(
                session, config=config, timeout=timeout
            )
        except (
            aiohttp.ClientError,
            TimeoutError,
            json.JSONDecodeError,
            KeyError,
        ) as exc:
            self._warn(f"{name}: failed to check ({exc})")
            return None
        if not latest:
            self._warn(f"{name}: could not determine latest version")
            return None
        return self._classify_update(name, current, latest)

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

    # ---------------------------------------------------------------- downloads

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
        self._info(f"Downloading {name}: {url}")
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
        timeout: int,
    ) -> None:
        """Download all updated vendor files in parallel, then update vendors.json."""
        base_dir = settings.VENDORS_FILE.parent
        tasks = [
            self._download_file(
                session,
                name=name,
                url=file_info["source"].format(version=latest),
                dest=base_dir / file_info["dest"],
                timeout=timeout,
            )
            for name, latest in updates
            for file_info in _iter_files(vendors[name])
        ]
        await asyncio.gather(*tasks)

        for name, latest in updates:
            vendors[name]["version"] = latest
            self._success(f"{name} updated to {latest}")

        self._save_vendors(vendors)
        self._success(f"Updated {settings.VENDORS_FILE.name}")


def _iter_files(config: VendorConfig) -> Iterator[VendorFile]:
    """Yield each VendorFile entry, normalising the flat source/dest form."""
    files = config.get("files")
    if files:
        yield from files
        return
    yield {"source": config.get("source", ""), "dest": config.get("dest", "")}


def _resolve_repo(config: VendorConfig) -> str | None:
    """Pick up an explicit `repo`, else derive from a github.com source URL."""
    repo = config.get("repo")
    if repo:
        return repo
    for file_info in _iter_files(config):
        if match := GITHUB_REPO_RE.match(file_info["source"]):
            return match.group(1)
    return None
