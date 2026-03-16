Project assistant for this django-studio generated project.

Determine the main package name from the "Project Layout" section of `AGENTS.md`.

## Usage

```
/djstudio <subcommand> [args]
```

Dispatch on the first word of $ARGUMENTS. Read the matching file and follow its
instructions exactly. If no subcommand is given, print the table below and stop.

**Generators**

| Subcommand                              | File                                          | Purpose                                                  |
|-----------------------------------------|-----------------------------------------------|----------------------------------------------------------|
| `create-app <app_name>`                 | `.claude/commands/djstudio/create-app.md`     | Scaffold a complete Django app                           |
| `create-view [<app_name>] <view>`       | `.claude/commands/djstudio/create-view.md`    | Add a view + template + URL (app optional for top-level views) |
| `create-task <app_name> <task>`         | `.claude/commands/djstudio/create-task.md`    | Add a background task using django-tasks-db              |
| `create-model <app_name> <model>`       | `.claude/commands/djstudio/create-model.md`   | Design a model with factory, fixture, and tests          |
| `create-crud <app_name> <model>`        | `.claude/commands/djstudio/create-crud.md`    | Full CRUD views, templates, URLs, and tests              |
| `create-e2e [<app_name>] <description>` | `.claude/commands/djstudio/create-e2e.md`     | Write Playwright E2E test(s) for a described interaction |

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

**Deployment**

| Subcommand | File                                     | Purpose                                                            |
|------------|------------------------------------------|--------------------------------------------------------------------|
| `launch`   | `.claude/commands/djstudio/launch.md`    | Interactive first-deploy wizard (infra → certs → secrets → deploy) |

**Maintenance**

| Subcommand           | File                                      | Purpose                                             |
|----------------------|-------------------------------------------|-----------------------------------------------------|
| `sync`               | `.claude/commands/djstudio/sync.md`       | Pull latest template changes via Copier and resolve merge conflicts |
| `feedback [description]` | `.claude/commands/djstudio/feedback.md` | File a GitHub issue against the django-studio repo |
