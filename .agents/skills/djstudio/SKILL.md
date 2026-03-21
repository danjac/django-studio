Project assistant for this django-studio generated project.

Determine the main package name from the "Project Layout" section of `AGENTS.md`.

## Usage

```
/djstudio <subcommand> [args]
```

Dispatch on the first word of $ARGUMENTS. Read the matching file and follow its
instructions exactly. If no subcommand is given, print the table below and stop.

**General**

| Subcommand           | File                                      | Purpose                                             |
|----------------------|-------------------------------------------|-----------------------------------------------------|
| `help [command]`     | `.agents/skills/djstudio/commands/help.md`       | Print user documentation for a subcommand          |
| `sync`               | `.agents/skills/djstudio/commands/sync.md`       | Pull latest template changes via Copier and resolve merge conflicts |
| `feedback [description]` | `.agents/skills/djstudio/commands/feedback.md` | File a GitHub issue against the django-studio repo |

**Generators**

| Subcommand                              | File                                          | Purpose                                                  |
|-----------------------------------------|-----------------------------------------------|----------------------------------------------------------|
| `create-app <app_name>`                 | `.agents/skills/djstudio/commands/create-app.md`     | Scaffold a complete Django app                           |
| `create-view [<app_name>] <view>`       | `.agents/skills/djstudio/commands/create-view.md`    | Add a view + template + URL (app optional for top-level views) |
| `create-task <app_name> <task>`         | `.agents/skills/djstudio/commands/create-task.md`    | Add a background task using django-tasks-db              |
| `create-command <app_name> [desc]`      | `.agents/skills/djstudio/commands/create-command.md` | Add a management command with tests; optionally enqueues tasks |
| `create-cron <app_name> <command>`      | `.agents/skills/djstudio/commands/create-cron.md`    | Schedule a management command as a Kubernetes cron job   |
| `create-model <app_name> <model>`       | `.agents/skills/djstudio/commands/create-model.md`   | Design a model with factory, fixture, and tests          |
| `create-crud <app_name> <model>`        | `.agents/skills/djstudio/commands/create-crud.md`    | Full CRUD views, templates, URLs, and tests              |
| `create-e2e [<app_name>] <description>` | `.agents/skills/djstudio/commands/create-e2e.md`     | Write Playwright E2E test(s) for a described interaction |
| `create-tag [<app_name>] [<module>]`    | `.agents/skills/djstudio/commands/create-tag.md`     | Add a template tag (simple_tag, simple_block_tag, inclusion_tag, or Node) |
| `create-filter [<app_name>] [<module>]` | `.agents/skills/djstudio/commands/create-filter.md`  | Add a template filter with correct escaping flags |

**Documentation**

| Subcommand                | File                                        | Purpose                                              |
|---------------------------|---------------------------------------------|------------------------------------------------------|
| `docs <topic>`            | `.agents/skills/djstudio/commands/docs.md`         | Look up or create project documentation              |
| `daisyui <component>`     | `.agents/skills/djstudio/commands/daisyui.md`      | Fetch DaisyUI component docs with project conventions |

**Localisation**

| Subcommand           | File                                        | Purpose                                       |
|----------------------|---------------------------------------------|-----------------------------------------------|
| `translate <locale>` | `.agents/skills/djstudio/commands/translate.md`    | Extract, translate, and compile message catalogue |

**Audits**

| Subcommand | File                                     | Purpose                                                  |
|------------|------------------------------------------|----------------------------------------------------------|
| `perf`     | `.agents/skills/djstudio/commands/perf.md`      | Performance audit: N+1 queries, indexes, caching, async  |
| `secure`   | `.agents/skills/djstudio/commands/secure.md`    | Security audit: settings, views, XSS, CSRF, IDOR, SQLi   |
| `gdpr`     | `.agents/skills/djstudio/commands/gdpr.md`      | GDPR compliance audit: PII, erasure, consent, logging    |
| `a11y`     | `.agents/skills/djstudio/commands/a11y.md`      | Accessibility audit: WCAG 2.1 AA — forms, icons, HTMX, Alpine, semantic HTML |
| `deadcode`       | `.agents/skills/djstudio/commands/deadcode.md`       | Remove unused Python code and static assets              |
| `full-coverage`  | `.agents/skills/djstudio/commands/full-coverage.md`  | Enable 100% coverage gate and write tests for all gaps   |

**Deployment**

| Subcommand        | File                                            | Purpose                                                            |
|-------------------|-------------------------------------------------|--------------------------------------------------------------------|
| `launch`                  | `.agents/skills/djstudio/commands/launch.md`                   | Interactive first-deploy wizard (infra → certs → secrets → deploy) |
| `launch-observability`    | `.agents/skills/djstudio/commands/launch-observability.md`     | Deploy the observability stack (Grafana + Prometheus + Loki)       |
| `rotate-secrets`          | `.agents/skills/djstudio/commands/rotate-secrets.md`           | Rotate auto-generated and third-party Helm secrets and redeploy    |
| `enable-db-backups`       | `.agents/skills/djstudio/commands/enable-db-backups.md`        | Enable automated daily PostgreSQL backups to Object Storage        |
