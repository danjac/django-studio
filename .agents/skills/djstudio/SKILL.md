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
| `help [command]`     | `.agents/skills/djstudio/help.md`       | Print user documentation for a subcommand          |
| `sync`               | `.agents/skills/djstudio/sync.md`       | Pull latest template changes via Copier and resolve merge conflicts |
| `feedback [description]` | `.agents/skills/djstudio/feedback.md` | File a GitHub issue against the django-studio repo |

**Generators**

| Subcommand                              | File                                          | Purpose                                                  |
|-----------------------------------------|-----------------------------------------------|----------------------------------------------------------|
| `create-app <app_name>`                 | `.agents/skills/djstudio/create-app.md`     | Scaffold a complete Django app                           |
| `create-view [<app_name>] <view>`       | `.agents/skills/djstudio/create-view.md`    | Add a view + template + URL (app optional for top-level views) |
| `create-task <app_name> <task>`         | `.agents/skills/djstudio/create-task.md`    | Add a background task using django-tasks-db              |
| `create-command <app_name> [desc]`      | `.agents/skills/djstudio/create-command.md` | Add a management command with tests; optionally enqueues tasks |
| `create-cron <app_name> <command>`      | `.agents/skills/djstudio/create-cron.md`    | Schedule a management command as a Kubernetes cron job   |
| `create-model <app_name> <model>`       | `.agents/skills/djstudio/create-model.md`   | Design a model with factory, fixture, and tests          |
| `create-crud <app_name> <model>`        | `.agents/skills/djstudio/create-crud.md`    | Full CRUD views, templates, URLs, and tests              |
| `create-e2e [<app_name>] <description>` | `.agents/skills/djstudio/create-e2e.md`     | Write Playwright E2E test(s) for a described interaction |
| `create-tag [<app_name>] [<module>]`    | `.agents/skills/djstudio/create-tag.md`     | Add a template tag (simple_tag, simple_block_tag, inclusion_tag, or Node) |
| `create-filter [<app_name>] [<module>]` | `.agents/skills/djstudio/create-filter.md`  | Add a template filter with correct escaping flags |

**Documentation**

| Subcommand                | File                                        | Purpose                                              |
|---------------------------|---------------------------------------------|------------------------------------------------------|
| `docs <topic>`            | `.agents/skills/djstudio/docs.md`         | Look up or create project documentation              |
| `daisyui <component>`     | `.agents/skills/djstudio/daisyui.md`      | Fetch DaisyUI component docs with project conventions |

**Localisation**

| Subcommand           | File                                        | Purpose                                       |
|----------------------|---------------------------------------------|-----------------------------------------------|
| `translate <locale>` | `.agents/skills/djstudio/translate.md`    | Extract, translate, and compile message catalogue |

**Audits**

| Subcommand | File                                     | Purpose                                                  |
|------------|------------------------------------------|----------------------------------------------------------|
| `perf`     | `.agents/skills/djstudio/perf.md`      | Performance audit: N+1 queries, indexes, caching, async  |
| `secure`   | `.agents/skills/djstudio/secure.md`    | Security audit: settings, views, XSS, CSRF, IDOR, SQLi   |
| `gdpr`     | `.agents/skills/djstudio/gdpr.md`      | GDPR compliance audit: PII, erasure, consent, logging    |
| `a11y`     | `.agents/skills/djstudio/a11y.md`      | Accessibility audit: WCAG 2.1 AA — forms, icons, HTMX, Alpine, semantic HTML |
| `deadcode`       | `.agents/skills/djstudio/deadcode.md`       | Remove unused Python code and static assets              |
| `full-coverage`  | `.agents/skills/djstudio/full-coverage.md`  | Enable 100% coverage gate and write tests for all gaps   |

**Deployment**

| Subcommand        | File                                            | Purpose                                                            |
|-------------------|-------------------------------------------------|--------------------------------------------------------------------|
| `launch`                  | `.agents/skills/djstudio/launch.md`                   | Interactive first-deploy wizard (infra → certs → secrets → deploy) |
| `launch-observability`    | `.agents/skills/djstudio/launch-observability.md`     | Deploy the observability stack (Grafana + Prometheus + Loki)       |
| `rotate-secrets`          | `.agents/skills/djstudio/rotate-secrets.md`           | Rotate auto-generated and third-party Helm secrets and redeploy    |
| `enable-db-backups`       | `.agents/skills/djstudio/enable-db-backups.md`        | Enable automated daily PostgreSQL backups to Object Storage        |
