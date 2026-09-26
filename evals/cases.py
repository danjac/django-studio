"""Eval case files: parsing and selection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = REPO_DIR / "evals" / "cases"

# A case whose prompt starts with this runs in an empty directory with the
# plugin loaded, instead of in a pre-rendered project.
BOOTSTRAP_SKILL = "/dj-bootstrap"


@dataclass
class Case:
    """A parsed eval case."""

    name: str
    prompt: str
    check: str
    review: str
    setup: str | None = None

    @property
    def bootstrap(self) -> bool:
        """True when the case creates the project itself with /dj-bootstrap."""
        return self.prompt.startswith(BOOTSTRAP_SKILL)


def select_cases(prefixes: list[str]) -> list[Case]:
    """Parse case files, filtered by file name prefix."""
    paths = sorted(CASES_DIR.glob("*.md"))
    if prefixes:
        paths = [p for p in paths if any(p.name.startswith(x) for x in prefixes)]
    return [parse_case(p) for p in paths]


def parse_case(path: Path) -> Case:
    """Extract the fenced block under each `## <Section>` heading."""
    sections: dict[str, str] = {}
    for match in re.finditer(
        r"^## (\w+)\s*\n.*?^```[a-z]*\n(.*?)^```", path.read_text(), re.M | re.S
    ):
        sections[match.group(1).lower()] = match.group(2)
    missing = {"prompt", "check", "review"} - sections.keys()
    if missing:
        raise SystemExit(f"{path.name}: missing sections {sorted(missing)}")
    return Case(
        name=path.stem,
        prompt=sections["prompt"].strip().replace("{template}", str(REPO_DIR)),
        check=sections["check"],
        review=sections["review"].strip(),
        setup=sections.get("setup"),
    )
