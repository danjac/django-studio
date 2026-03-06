#!/usr/bin/env python
"""Post-generation hook: adjusts files based on cookiecutter choices.

Most feature-flag logic is handled by Jinja2 conditionals in the template
files themselves (settings.py, urls.py, views.py, pyproject.toml, .env.example).

This hook handles only what Jinja2 cannot:
- HTML template manipulation (files in _copy_without_render)
- File/directory creation and deletion
- Justfile PROJECT_SLUG replacement (_copy_without_render)
- Skill installation and uv lock
- Claude Code settings.json with agentic hooks
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

PROJECT_SLUG = "{{cookiecutter.project_slug}}"
USE_HX_BOOST = "{{cookiecutter.use_hx_boost}}"
USE_STORAGE = "{{cookiecutter.use_storage}}"
USE_PWA = "{{cookiecutter.use_pwa}}"
USE_OPENTELEMETRY = "{{cookiecutter.use_opentelemetry}}"
USE_SENTRY = "{{cookiecutter.use_sentry}}"

BASE_DIR = Path()

TEMPLATES_DIR = BASE_DIR / "templates"
BASE_HTML = TEMPLATES_DIR / "base.html"
DEFAULT_BASE_HTML = TEMPLATES_DIR / "default_base.html"
HX_BASE_HTML = TEMPLATES_DIR / "hx_base.html"

JUSTFILE = BASE_DIR / "justfile"
TERRAFORM_STORAGE_DIR = BASE_DIR / "terraform" / "storage"
OBSERVABILITY_HELM_DIR = BASE_DIR / "helm" / "observability"
SERVICE_WORKER_JS = BASE_DIR / "static" / "service-worker.js"

# Markers in default_base.html (which is _copy_without_render).
# These use [[ ]] syntax so Jinja2 ignores them during hook rendering.
_MARKER_BODY_OPEN = "  [[ HOOK:body-open ]]"
_MARKER_PWA_MANIFEST = "    [[ HOOK:pwa-manifest ]]"
_MARKER_PWA_SW = "    [[ HOOK:pwa-sw ]]"

_BODY_PLAIN = "  <body>"
_BODY_HX_BOOST = '  <body\n    hx-boost="true">'

# Django template syntax must be wrapped in a raw block so Jinja2 does not
# process it when rendering this hook file.
{% raw %}
_PWA_MANIFEST_LINK = '    <link rel="manifest" href="{% url \'manifest\' %}">'

_PWA_SW_SCRIPT = """\
    <script>
      if (typeof navigator.serviceWorker !== 'undefined') {
        navigator.serviceWorker.register('{% static "service-worker.js" %}')
      }
    </script>"""
{% endraw %}


def _replace_marker(content: str, marker: str, replacement: str) -> str:
    """Replace a marker line with replacement content, removing the line if empty."""
    if replacement:
        return content.replace(marker, replacement)
    # Remove the entire line (including newline) when replacement is empty
    return content.replace(marker + "\n", "")


def resolve_markers() -> None:
    """Replace all marker comments in default_base.html with actual content.

    This runs BEFORE any file renames so default_base.html always exists.
    """
    with DEFAULT_BASE_HTML.open() as f:
        content = f.read()

    # Body tag: add hx-boost attribute when enabled
    body_replacement = _BODY_HX_BOOST if USE_HX_BOOST == "y" else _BODY_PLAIN
    content = _replace_marker(content, _MARKER_BODY_OPEN, body_replacement)

    # PWA manifest link: insert before CSS link when enabled
    pwa_manifest = _PWA_MANIFEST_LINK if USE_PWA == "y" else ""
    content = _replace_marker(content, _MARKER_PWA_MANIFEST, pwa_manifest)

    # PWA service worker script: insert before </body> when enabled
    pwa_sw = _PWA_SW_SCRIPT if USE_PWA == "y" else ""
    content = _replace_marker(content, _MARKER_PWA_SW, pwa_sw)

    with DEFAULT_BASE_HTML.open("w") as f:
        f.write(content)


# ── hx-boost ─────────────────────────────────────────────────────────────────


def enable_hx_boost() -> None:
    """Wire up hx-boost: base.html dynamically extends hx_base or default_base."""
    with BASE_HTML.open("w") as f:
        f.write(
            "{" + '% extends request.htmx|yesno:"hx_base.html,default_base.html" %}\n'
        )


def remove_hx_base() -> None:
    """Collapse default_base.html into base.html when hx-boost is not used.

    Without hx-boost there is no need for dynamic extends; base.html becomes
    the full layout and the default_base.html / hx_base.html stubs are removed.
    """
    if HX_BASE_HTML.exists():
        HX_BASE_HTML.unlink()
    DEFAULT_BASE_HTML.replace(BASE_HTML)


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
    if os.path.exists(SERVICE_WORKER_JS):
        os.remove(SERVICE_WORKER_JS)


# ── skills ───────────────────────────────────────────────────────────────────


def install_claude_hooks() -> None:
    """Write .claude/settings.json with agentic hooks for the generated project."""
    settings = {
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
                                " — fix the pre-commit issue instead.' >&2; exit 2; fi"
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
                                " — run: just dj makemigrations'; fi"
                            ),
                        },
                    ],
                }
            ],
        }
    }
    claude_dir = BASE_DIR / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    settings_file = claude_dir / "settings.json"
    with settings_file.open("w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


def install_skills() -> None:
    """Copy skills from the template's skills/ directory to .claude/commands/."""
    skills_src = Path("{{cookiecutter._repo_dir}}") / "skills"
    if not skills_src.is_dir():
        return
    commands_dst = BASE_DIR / ".claude" / "commands"
    commands_dst.mkdir(parents=True, exist_ok=True)
    for skill_file in skills_src.glob("*.md"):
        shutil.copy(skill_file, commands_dst / skill_file.name)


# ── main ─────────────────────────────────────────────────────────────────────

# 1. Resolve all HTML marker comments (must happen before file renames)
resolve_markers()

# 2. Feature-flag file operations
if USE_HX_BOOST == "y":
    enable_hx_boost()
else:
    remove_hx_base()

if USE_STORAGE != "y":
    remove_storage_terraform()

if USE_OPENTELEMETRY != "y":
    remove_observability_helm()

if USE_PWA != "y":
    remove_pwa_static()

# 3. Inject project slug into justfile (which is _copy_without_render)
with JUSTFILE.open() as f:
    content = f.read()
with JUSTFILE.open("w") as f:
    f.write(content.replace("PROJECT_SLUG", PROJECT_SLUG))

# 4. Install skills, Claude hooks, and generate lock file
install_skills()
install_claude_hooks()

# Generate uv.lock so CI's `uv sync --frozen` works without an extra manual step
subprocess.run(["uv", "lock"], check=True)
