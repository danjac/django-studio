#!/usr/bin/env python
"""Post-generation hook: adjusts files based on copier choices.

This hook handles what Jinja2 cannot:
- GitHub Actions workflow name substitution (files contain ${{ }} GHA syntax
  which conflicts with Jinja2, so PROJECT_SLUG is used as a plain placeholder)
- License file installation
- Skill installation and Claude Code settings.json generation
- uv lock file generation

Invoked by copier as:
    python hooks/post_gen_project.py <project_slug> <license> <author>
"""

import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

_, PROJECT_SLUG, *_args = sys.argv
LICENSE = _args[0] if _args else "None"
AUTHOR = _args[1] if len(_args) > 1 else ""

# Template source root: hooks/post_gen_project.py → hooks/ → template root
_TEMPLATE_ROOT = Path(sys.argv[0]).resolve().parent.parent

BASE_DIR = Path()

# Generated config files backed up before each copier update so dj-sync can diff them.
BACKUP_FILES = [
    BASE_DIR / ".claude" / "settings.json",
    BASE_DIR / ".mcp.json",
    BASE_DIR / "opencode.json",
]

# Files containing PROJECT_SLUG as a plain-text placeholder. These cannot be
# .jinja templates because they use ${{ }}, {{ args }}, or other syntax that
# conflicts with Jinja2.
PLAIN_SLUG_FILES = [
    BASE_DIR / "justfile",
    BASE_DIR / ".agents" / "skills" / "dj-db-backup" / "bin" / "db-backup.sh",
    BASE_DIR / ".agents" / "skills" / "dj-db-restore" / "bin" / "db-restore.sh",
    BASE_DIR / ".agents" / "skills" / "dj-db-restore" / "bin" / "list-backups.sh",
    *[
        BASE_DIR / ".github" / "workflows" / name
        for name in (
            "build.yml",
            "checks.yml",
            "default.yml",
            "docker.yml",
            "deploy.yml",
        )
    ],
]


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


def _parse_skill_description(skill_file: Path) -> str:
    """Return the description from YAML frontmatter in a SKILL.md file."""
    content = skill_file.read_text()
    if not content.startswith("---\n"):
        return ""
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        return ""
    for line in parts[1].splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip(' "')
    return ""


def _next_backup_dir() -> Path:
    """Return .django_studio/backups/<n>/ where n is one higher than the current maximum."""
    backup_root = BASE_DIR / ".django_studio" / "backups"
    existing = (
        [int(d.name) for d in backup_root.iterdir() if d.is_dir() and d.name.isdigit()]
        if backup_root.exists()
        else []
    )
    return backup_root / str(max(existing, default=0) + 1)


def _backup_files(backup_dir: Path) -> None:
    """Copy existing BACKUP_FILES into backup_dir preserving relative paths.

    dj-sync diffs each backup against its counterpart in the project root.
    """
    for src in BACKUP_FILES:
        if src.exists():
            dest = backup_dir / src.relative_to(BASE_DIR)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def install_claude_hooks() -> None:
    """Write .claude/settings.json with permissions and agentic hooks."""
    settings = {
        "permissions": {
            "allow": [
                "Bash(just lint:*)",
                "Bash(just test:*)",
                "Bash(just test-all:*)",
                "Bash(just test-e2e:*)",
                "Bash(just check-all:*)",
                "Bash(just typecheck:*)",
                "Bash(just dj:*)",
                "Bash(just start:*)",
                "Bash(just stop:*)",
                "Bash(just serve:*)",
                "Bash(just psql:*)",
                "Bash(just tw:*)",
                "Bash(just precommit:*)",
                "Bash(just dc:*)",
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
                    "matcher": "mcp__playwright__browser_navigate",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                "if ! pgrep -f 'manage.py runserver' > /dev/null 2>&1;"
                                f" then just serve > /tmp/{PROJECT_SLUG}-serve.log 2>&1 & sleep 3; fi"
                            ),
                            "statusMessage": "Ensuring dev server is running...",
                        }
                    ],
                },
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
                        },
                        {
                            "type": "command",
                            "command": (
                                "CMD=$(jq -r '.tool_input.command');"
                                " if echo \"$CMD\" | grep -qE 'git commit';"
                                " then echo 'Running just check-all before commit...' >&2;"
                                " just check-all >&2 || { echo 'BLOCKED: just check-all failed"
                                " — fix errors before committing.' >&2; exit 2; }; fi"
                            ),
                        },
                    ],
                },
            ],
            "PostToolUse": [
                {
                    "matcher": "Edit|Write",
                    "hooks": [
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
        },
    }
    claude_dir = BASE_DIR / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    with (claude_dir / "settings.json").open("w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    commands_dst = claude_dir / "commands"
    commands_dst.mkdir(parents=True, exist_ok=True)
    skills_root = BASE_DIR / ".agents" / "skills"
    opencode_commands: dict[str, dict[str, str]] = {}
    for skill_dir in sorted(skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        name = skill_dir.name
        (commands_dst / f"{name}.md").write_text(f"@.agents/skills/{name}/SKILL.md\n")
        description = _parse_skill_description(skill_file)
        opencode_commands[name] = {
            "template": f".agents/skills/{name}/SKILL.md",
            "description": description,
        }
    opencode = {
        "$schema": "https://opencode.ai/config.json",
        "command": opencode_commands,
    }
    with (BASE_DIR / "opencode.json").open("w") as f:
        json.dump(opencode, f, indent=2)
        f.write("\n")


# ── MCP config ───────────────────────────────────────────────────────────────


def install_mcp_config() -> None:
    """Write .mcp.json with project-local MCP servers (gitignored)."""
    config = {
        "mcpServers": {
            "postgres": {
                "command": "sh",
                "args": [
                    "-c",
                    "set -a; . ./.env; set +a;"
                    ' npx -y @modelcontextprotocol/server-postgres "$DATABASE_URL"',
                ],
            },
            "playwright": {
                "command": "npx",
                "args": ["@playwright/mcp"],
            },
            "django": {
                "command": "uv",
                "args": ["run", "python", "-m", "mcp_django"],
                "env": {"DJANGO_SETTINGS_MODULE": "config.settings"},
            },
        }
    }
    with (BASE_DIR / ".mcp.json").open("w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


# ── main ─────────────────────────────────────────────────────────────────────

# 1. Install license file
install_license()

# 3. Substitute PROJECT_SLUG in files that cannot be .jinja templates because
#    they use ${{ }}, {{ args }}, or other syntax that conflicts with Jinja2.
for path in PLAIN_SLUG_FILES:
    if path.exists():
        path.write_text(path.read_text().replace("PROJECT_SLUG", PROJECT_SLUG))

# 4. Back up generated config files, then regenerate them
_backup_dir = _next_backup_dir()
_backup_files(_backup_dir)
if _backup_dir.exists():
    print(f"Backed up generated config files to {_backup_dir}")
install_claude_hooks()
install_mcp_config()

# Generate uv.lock so CI's `uv sync --frozen` works without a manual step
subprocess.run(["uv", "lock"], check=True)
