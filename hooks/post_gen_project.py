#!/usr/bin/env python
"""Post-generation hook: adjusts files based on copier choices.

Most feature-flag logic is handled by Jinja2 conditionals in the template
files themselves (settings.py, urls.py, views.py, pyproject.toml, .env.example).

This hook handles only what Jinja2 cannot:
- HTML template manipulation (base.html uses marker comments)
- File/directory creation and deletion based on feature flags
- GitHub Actions workflow name substitution (files contain ${{ }} GHA syntax
  which conflicts with Jinja2, so PROJECT_SLUG is used as a plain placeholder)
- License file installation
- Skill installation and Claude Code settings.json generation
- uv lock file generation

Invoked by copier as:
    python hooks/post_gen_project.py <project_slug> <use_storage>
                                     <use_pwa> <use_opentelemetry> <use_sentry>
                                     <license> <author>
"""

import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

_, PROJECT_SLUG, *_args = sys.argv
USE_STORAGE, USE_PWA, USE_OPENTELEMETRY, USE_SENTRY = (
    f == "True" for f in _args[:4]
)
LICENSE = _args[4] if len(_args) > 4 else "None"
AUTHOR = _args[5] if len(_args) > 5 else ""

# Template source root: hooks/post_gen_project.py → hooks/ → template root
_TEMPLATE_ROOT = Path(sys.argv[0]).resolve().parent.parent

BASE_DIR = Path()

TEMPLATES_DIR = BASE_DIR / "templates"
BASE_HTML = TEMPLATES_DIR / "base.html"

DEPLOY_WORKFLOW = BASE_DIR / ".github" / "workflows" / "deploy.yml"
# Files containing PROJECT_SLUG as a plain-text placeholder. These cannot be
# .jinja templates because they use ${{ }}, {{ args }}, or other syntax that
# conflicts with Jinja2.
PLAIN_SLUG_FILES = [
    BASE_DIR / "justfile",
    *[
        BASE_DIR / ".github" / "workflows" / name
        for name in ("build.yml", "checks.yml", "default.yml", "docker.yml", "deploy.yml")
    ],
]
TERRAFORM_STORAGE_DIR = BASE_DIR / "terraform" / "storage"
OBSERVABILITY_HELM_DIR = BASE_DIR / "helm" / "observability"
SERVICE_WORKER_JS = BASE_DIR / "static" / "service-worker.js"

# Markers in base.html (plain text, not Jinja2, so no conflict).
_MARKER_PWA_MANIFEST = "    [[ HOOK:pwa-manifest ]]"
_MARKER_PWA_SW = "    [[ HOOK:pwa-sw ]]"

_PWA_MANIFEST_LINK = '    <link rel="manifest" href="{% url \'manifest\' %}">'

_PWA_SW_SCRIPT = """\
    <script>
      if (typeof navigator.serviceWorker !== 'undefined') {
        navigator.serviceWorker.register('{% static "service-worker.js" %}')
      }
    </script>"""


def _replace_marker(content: str, marker: str, replacement: str) -> str:
    """Replace a marker line with replacement content, removing the line if empty."""
    if replacement:
        return content.replace(marker, replacement)
    return content.replace(marker + "\n", "")


def resolve_markers() -> None:
    """Replace all marker comments in base.html with actual content."""
    with BASE_HTML.open() as f:
        content = f.read()

    pwa_manifest = _PWA_MANIFEST_LINK if USE_PWA else ""
    content = _replace_marker(content, _MARKER_PWA_MANIFEST, pwa_manifest)

    pwa_sw = _PWA_SW_SCRIPT if USE_PWA else ""
    content = _replace_marker(content, _MARKER_PWA_SW, pwa_sw)

    with BASE_HTML.open("w") as f:
        f.write(content)


# ── storage ──────────────────────────────────────────────────────────────────


def remove_storage_terraform() -> None:
    """Remove the storage terraform directory when storage is not used."""
    if TERRAFORM_STORAGE_DIR.is_dir():
        shutil.rmtree(TERRAFORM_STORAGE_DIR)


# ── observability ────────────────────────────────────────────────────────────


def remove_observability_helm() -> None:
    """Remove the observability helm chart when OpenTelemetry is not used."""
    if OBSERVABILITY_HELM_DIR.is_dir():
        shutil.rmtree(OBSERVABILITY_HELM_DIR)


# ── pwa ──────────────────────────────────────────────────────────────────────


def remove_pwa_static() -> None:
    """Remove the service worker when PWA is not used."""
    if SERVICE_WORKER_JS.exists():
        SERVICE_WORKER_JS.unlink()


# ── license ──────────────────────────────────────────────────────────────────


def install_license() -> None:
    """Copy the chosen license file to LICENSE, substituting year and author."""
    if LICENSE == "None":
        return
    src = _TEMPLATE_ROOT / "licenses" / LICENSE
    if not src.exists():
        return
    year = str(datetime.date.today().year)
    text = src.read_text().replace("[YEAR]", year).replace("[AUTHOR]", AUTHOR)
    (BASE_DIR / "LICENSE").write_text(text)


# ── skills ───────────────────────────────────────────────────────────────────


def install_claude_hooks() -> None:
    """Write .claude/settings.json with permissions and agentic hooks."""
    settings = {
        "permissions": {
            "allow": [
                "Bash(just:*)",
                "Bash(git status:*)",
                "Bash(git log:*)",
                "Bash(git diff:*)",
                "Bash(git show:*)",
                "Bash(rg:*)",
                "Bash(fd:*)",
                "Bash(ast-grep:*)",
            ]
        },
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                "CMD=$(jq -r '.tool_input.command');"
                                " if echo \"$CMD\" | grep -q -- '--no-verify';"
                                " then echo 'BLOCKED: --no-verify is forbidden"
                                " - fix the pre-commit issue instead.' >&2; exit 2; fi"
                            ),
                        }
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Edit|Write",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                "FILE=$(jq -r '.tool_input.file_path // empty');"
                                " if [ -n \"$FILE\" ]"
                                " && echo \"$FILE\" | grep -q '\\.py$'"
                                " && ! echo \"$FILE\" | grep -q '/migrations/';"
                                " then uv run ruff check --fix \"$FILE\""
                                " && uv run ruff format \"$FILE\"; fi"
                            ),
                        },
                        {
                            "type": "command",
                            "command": (
                                "FILE=$(jq -r '.tool_input.file_path // empty');"
                                " if echo \"$FILE\" | grep -qE '/models[^/]*\\.py$';"
                                " then echo 'REMINDER: models file edited"
                                " - run: just dj makemigrations'; fi"
                            ),
                        },
                    ],
                }
            ],
        },
    }
    claude_dir = BASE_DIR / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    with (claude_dir / "settings.json").open("w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


def install_skills() -> None:
    """Copy skills from the template's skills/ directory to .claude/commands/."""
    skills_src = _TEMPLATE_ROOT / "skills"
    if not skills_src.is_dir():
        return
    commands_dst = BASE_DIR / ".claude" / "commands"
    commands_dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skills_src, commands_dst, dirs_exist_ok=True)


# ── main ─────────────────────────────────────────────────────────────────────

# 1. Resolve HTML marker comments in base.html
resolve_markers()

# 2. Feature-flag file operations
if not USE_STORAGE:
    remove_storage_terraform()

if not USE_OPENTELEMETRY:
    remove_observability_helm()

if not USE_PWA:
    remove_pwa_static()

install_license()

# 3. Substitute PROJECT_SLUG in files that cannot be .jinja templates because
#    they use ${{ }}, {{ args }}, or other syntax that conflicts with Jinja2.
for path in PLAIN_SLUG_FILES:
    if path.exists():
        path.write_text(path.read_text().replace("PROJECT_SLUG", PROJECT_SLUG))

# 4. Install skills, Claude hooks, and generate lock file
install_skills()
install_claude_hooks()

# Generate uv.lock so CI's `uv sync --frozen` works without a manual step
subprocess.run(["uv", "lock"], check=True)
