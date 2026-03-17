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
| `help [command]`     | `.claude/commands/djstudio/help.md`       | Print user documentation for a subcommand          |
| `sync`               | `.claude/commands/djstudio/sync.md`       | Pull latest template changes via Copier and resolve merge conflicts |
| `feedback [description]` | `.claude/commands/djstudio/feedback.md` | File a GitHub issue against the django-studio repo |

**Generators**

| Subcommand                              | File                                          | Purpose                                                  |
|-----------------------------------------|-----------------------------------------------|----------------------------------------------------------|
| `create-app <app_name>`                 | `.claude/commands/djstudio/create-app.md`     | Scaffold a complete Django app                           |
| `create-view [<app_name>] <view>`       | `.claude/commands/djstudio/create-view.md`    | Add a view + template + URL (app optional for top-level views) |
| `create-task <app_name> <task>`         | `.claude/commands/djstudio/create-task.md`    | Add a background task using django-tasks-db              |
| `create-command <app_name> [desc]`      | `.claude/commands/djstudio/create-command.md` | Add a management command with tests; optionally enqueues tasks |
| `create-cron <app_name> <command>`      | `.claude/commands/djstudio/create-cron.md`    | Schedule a management command as a Kubernetes cron job   |
| `create-model <app_name> <model>`       | `.claude/commands/djstudio/create-model.md`   | Design a model with factory, fixture, and tests          |
| `create-crud <app_name> <model>`        | `.claude/commands/djstudio/create-crud.md`    | Full CRUD views, templates, URLs, and tests              |
| `create-e2e [<app_name>] <description>` | `.claude/commands/djstudio/create-e2e.md`     | Write Playwright E2E test(s) for a described interaction |
| `create-tag [<app_name>] [<module>]`    | `.claude/commands/djstudio/create-tag.md`     | Add a template tag (simple_tag, simple_block_tag, inclusion_tag, or Node) |
| `create-filter [<app_name>] [<module>]` | `.claude/commands/djstudio/create-filter.md`  | Add a template filter with correct escaping flags |

**Localisation**

| Subcommand           | File                                        | Purpose                                       |
|----------------------|---------------------------------------------|-----------------------------------------------|
| `translate <locale>` | `.claude/commands/djstudio/translate.md`    | Extract, translate, and compile message catalogue |

**Audits**

| Subcommand | File                                     | Purpose                                                  |
|------------|------------------------------------------|----------------------------------------------------------|
| `perf`     | `.claude/commands/djstudio/perf.md`      | Performance audit: N+1 queries, indexes, caching, async  |
| `secure`   | `.claude/commands/djstudio/secure.md`    | Security audit: settings, views, XSS, CSRF, IDOR, SQLi   |
| `gdpr`     | `.claude/commands/djstudio/gdpr.md`      | GDPR compliance audit: PII, erasure, consent, logging    |
| `a11y`     | `.claude/commands/djstudio/a11y.md`      | Accessibility audit: WCAG 2.1 AA — forms, icons, HTMX, Alpine, semantic HTML |
| `deadcode` | `.claude/commands/djstudio/deadcode.md`  | Remove unused Python code and static assets              |

**Deployment**

| Subcommand        | File                                            | Purpose                                                            |
|-------------------|-------------------------------------------------|--------------------------------------------------------------------|
| `launch`          | `.claude/commands/djstudio/launch.md`           | Interactive first-deploy wizard (infra → certs → secrets → deploy) |
| `rotate-secrets`  | `.claude/commands/djstudio/rotate-secrets.md`   | Rotate auto-generated and third-party Helm secrets and redeploy    |
