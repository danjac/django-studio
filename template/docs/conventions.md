# Conventions

This page lists the names, versions and connection details that more than one file
depends on. **If another doc or skill disagrees with this page, this page wins.** Fix
the other doc, or fix this page if the code has changed.

Other docs link here instead of restating these values. When you change one of them,
update every file listed for it in the same commit, then update this page.

## Contents

- [Version Pins](#version-pins)
- [Environment Variables](#environment-variables)
- [Redis Databases](#redis-databases)
- [Service Names](#service-names)
- [Test Settings](#test-settings)

## Version Pins

Version numbers live in the files below, not in docs. When you bump a component, change
every file in its row in the same commit.

| Component | Files that must change together |
|-----------|---------------------------------|
| Python | `pyproject.toml` (`requires-python`, ruff `target-version`), `.pre-commit-config.yaml` (pyupgrade `--py3XX`), `Dockerfile` (`ARG PYTHON_IMAGE`), `.github/workflows/checks.yml` (`python-version` and `uv python install`) |
| Django | `pyproject.toml` (`django` dependency), `.pre-commit-config.yaml` (django-upgrade `--target-version`) |
| PostgreSQL | `docker-compose.yml` (`postgres` image), `helm/site/values.yaml` (`postgres.image`), `.github/workflows/checks.yml` (both `services.postgres.image`), `Dockerfile` (`ARG POSTGRES_MAJOR`, major only) |
| Redis | `docker-compose.yml` (`redis` image), `helm/site/values.yaml` (`redis.image`) |
| uv | `Dockerfile` (`ARG UV_VERSION`), `.github/workflows/checks.yml` (`env.UV_VERSION`), `.pre-commit-config.yaml` (`astral-sh/uv-pre-commit` rev) |

The Helm chart derives the PostgreSQL major version from the `postgres.image` tag
(`app.postgresVersion` in `helm/site/templates/_helpers.tpl`) and uses it in the PV and
PVC names. A major version change is an upgrade, not a pin bump: follow
[Upgrade PostgreSQL major version](deployment.md#upgrade-postgresql-major-version).

## Environment Variables

`config/settings.py` is the authority for which variables exist and their defaults.
`.env.example` lists the ones used in local development.

Connection URLs:

| Variable | Local default | Production value (built in `helm/site/templates/secret.yaml`) |
|----------|---------------|------------------------------------------------------------|
| `DATABASE_URL` | `postgresql://postgres:password@127.0.0.1:5432/postgres` | `postgresql://postgres:<password>@postgres.<namespace>.svc.cluster.local:5432/postgres` |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | `redis://default:<password>@redis.<namespace>.svc.cluster.local:6379/0` |
| `EMAIL_URL` | `smtp://localhost:1025` | not set; production sends through Mailgun (`MAILGUN_API_KEY`) |

The production URL formats are also rebuilt by
`.agents/skills/dj-rotate-secrets/scripts/patch-k8s-secrets.sh`. Keep it in step with
`secret.yaml`.

Naming rules:

- Feature flags are booleans named `USE_<FEATURE>` (`USE_HTTPS`, `USE_CONNECTION_POOL`,
  `USE_ZEAL`).
- Connection strings are named `<SERVICE>_URL`.
- Host ports published by `docker-compose.yml` are named `<SERVICE>_PORT`
  (`POSTGRES_PORT`, `REDIS_PORT`, `MAILPIT_WEB_PORT`, `MAILPIT_SMTP_PORT`).
- In production, secrets go in the `secrets` Secret (`helm/site/templates/secret.yaml`)
  and everything else goes in the `configmap` ConfigMap
  (`helm/site/templates/configmap.yaml`).

## Redis Databases

| DB | Consumer | Configured by |
|----|----------|---------------|
| 0 | Django cache (including `cached_db` sessions) | `CACHES["default"]` from `REDIS_URL` |
| 0 | Channels layer, if you add [Channels](channels.md) | `CHANNEL_LAYERS` from `REDIS_URL` |

Background tasks use the database (`django-tasks-db`), not Redis.

To give a new consumer its own database, use the next free number and add a row here.

## Service Names

The same names are used in Docker Compose (local) and in Kubernetes (production), so
connection URLs differ only by host.

| Service | Compose service | Kubernetes resources | Port |
|---------|-----------------|----------------------|------|
| PostgreSQL | `postgres` | StatefulSet and Service `postgres` | 5432 |
| Redis | `redis` | Deployment and Service `redis` | 6379 |
| Mailpit (dev only) | `mailpit` | none | 8025 (web), 1025 (SMTP) |
| Web app | none (`just serve`) | Deployment `django-app`, Service `django` | 8000 |
| Task worker | none (`just dj db_worker`) | Deployment `django-worker` | none |
| Release (migrations) | none | Job `django-release` | none |
| Database backups | none | CronJob `postgres-backup` | none |

Inside the cluster, services are reached at `<service>.<namespace>.svc.cluster.local`.

## Test Settings

There is no separate test settings module. Both test runs use `config.settings`:

- Unit tests: `[tool.pytest.ini_options]` in `pyproject.toml`
  (`DJANGO_SETTINGS_MODULE = "config.settings"`, `-m "not e2e"`).
- E2E tests: `playwright.ini` (`DJANGO_SETTINGS_MODULE = config.settings`, `-m e2e`).
  It sets environment overrides under `env =` (a placeholder `SECRET_KEY`,
  `USE_ZEAL=false` and the `USE_*` production flags turned off) so E2E tests run
  without a `.env`.

Change behaviour for tests with environment variables in these files, not with a new
settings module.
