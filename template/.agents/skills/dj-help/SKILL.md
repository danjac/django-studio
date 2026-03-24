Print documentation for dj-* commands.

Parse `$ARGUMENTS` as: `[command_name]`

If no `command_name` is given:
1. Print the full command table below.
2. Stop — do not execute any other instructions.

Otherwise:
1. Read `.agents/skills/dj-<command_name>/SKILL.md`.
   If the file does not exist, say:
   > Unknown command: `/dj-<command_name>`. Run `/dj-help` for a list of commands.
   Then stop.
2. Find the `## Help` section in that file.
3. Print its contents verbatim to the user.
4. Stop — do not execute any other instructions in the file.

---

## Commands

**General**

| Command | Purpose |
|---------|---------|
| `/dj-help [command]` | List all commands, or show docs for a command |
| `/dj-sync` | Pull latest template changes via Copier |
| `/dj-feedback [description]` | File a GitHub issue against the django-studio repo |

**Generators**

| Command | Purpose |
|---------|---------|
| `/dj-create-app <app_name>` | Scaffold a complete Django app |
| `/dj-create-view [<app_name>] <view>` | Add a view + template + URL |
| `/dj-create-task <app_name> <task>` | Add a background task using django-tasks-db |
| `/dj-create-command <app_name> [desc]` | Add a management command with tests |
| `/dj-create-cron <app_name> <command>` | Schedule a management command as a Kubernetes cron job |
| `/dj-create-model <app_name> <model>` | Design a model with factory, fixture, and tests |
| `/dj-create-crud <app_name> <model>` | Full CRUD views, templates, URLs, and tests |
| `/dj-create-e2e [<app_name>] <description>` | Write Playwright E2E test(s) |
| `/dj-create-tag [<app_name>] [<module>]` | Add a template tag |
| `/dj-create-filter [<app_name>] [<module>]` | Add a template filter |

**Localisation**

| Command | Purpose |
|---------|---------|
| `/dj-translate <locale>` | Extract, translate, and compile message catalogue |

**Audits**

| Command | Purpose |
|---------|---------|
| `/dj-perf` | Performance audit: N+1 queries, indexes, caching, async |
| `/dj-secure` | Security audit: settings, views, XSS, CSRF, IDOR, SQLi |
| `/dj-gdpr` | GDPR compliance audit: PII, erasure, consent, logging |
| `/dj-a11y` | Accessibility audit: WCAG 2.1 AA |
| `/dj-deadcode` | Remove unused Python code, templates, and static assets |
| `/dj-full-coverage` | Enable 100% coverage gate and write tests for all gaps |

**Deployment**

| Command | Purpose |
|---------|---------|
| `/dj-launch` | Interactive first-deploy wizard |
| `/dj-launch-observability` | Deploy the observability stack |
| `/dj-rotate-secrets` | Rotate auto-generated and third-party Helm secrets |
| `/dj-enable-db-backups` | Enable automated daily PostgreSQL backups |

---

## Help

**/dj-help [command]**

Lists all available dj-* commands, or shows documentation for a specific command.

With no argument, prints the full command table. With a command name, reads
`.agents/skills/dj-<command>/SKILL.md` and prints its `## Help` section verbatim.

Examples:
  /dj-help
  /dj-help create-cron
  /dj-help create-model
