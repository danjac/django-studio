---
description: Create or update project-specific docs (domain, apps, rules, APIs)
---

Write or refresh documentation about **this project** — what it does, its domain,
its apps, business rules, APIs and integrations. This is different from the generic
`docs/*.md` pages, which describe how to build things with the stack (HTMX, models,
migrations) and are owned by the template.

Arguments: `$ARGUMENTS`

- No argument — the whole project: `docs/this-project.md` plus every app README.
- `<app_name>` — only `<package_name>/<app_name>/README.md` (and the app's row in
  `docs/this-project.md`).

The skill is **idempotent**: the first run creates the docs, later runs update them.
It never changes code.

---

## Where project docs live

Follows Locality of Behaviour (`docs/project-structure.md#locality-of-behaviour`):

| File | Contents |
| ---- | -------- |
| `docs/this-project.md` | Project overview: purpose, users, glossary, app map, key flows, integrations, decisions |
| `<package_name>/<app>/README.md` | One per app: purpose, business rules, lifecycles, API, integrations, reference |

The structure for each file is fixed:

- `docs/this-project.md` — use the headings already in the file (the template ships a
  stub with guidance under each heading).
- App READMEs — use `references/app-readme.md`.

Do not add project docs anywhere else under `docs/`, and do not edit the generic
`docs/*.md` pages — they are owned by the template and updated by `/dj-sync`, so
project content there causes merge conflicts.

## Authored vs derived content

Every section is one of two kinds. Treat them differently on update.

| Kind | Source | On update |
| ---- | ------ | --------- |
| **Authored** | The user (answers to questions) | Never rewrite or delete silently. If code now contradicts it, ask. |
| **Derived** | The code | Regenerate freely from the current code. |

- Authored: Purpose, Users and roles, Glossary, Key flows, Key decisions, the *rule
  text* in Business rules, Lifecycle meaning, Gotchas.
- Derived: App map, Integrations table, the *Enforced in* column of Business rules,
  API endpoints, Background work, Personal data locations, Reference.

Sections that mix both (e.g. Business rules) keep authored text and refresh derived
columns.

---

## 1. Read before writing

1. Read `docs/project-structure.md` and `docs/this-project.md`.
2. If `docs/this-project.md` still contains the line `<!-- dj-doc: stub -->`, this is a
   **first run** for the overview — replace the stub guidance with real content.
3. For each app in scope, check whether `<package_name>/<app>/README.md` exists —
   **update** it if so, **create** it from `references/app-readme.md` if not.

## 2. Discover

For each app in scope (Django apps under `<package_name>/` listed in
`INSTALLED_APPS`), collect facts from the code. Use `rg` / `ast-grep`; do not guess.

| Look for | Where |
| -------- | ----- |
| Models, choices/status fields, constraints | `models.py` |
| Querysets used as access gates (`for_owner`, `for_member`) | `models.py` |
| Permissions and predicates | `rules.py` |
| HTML routes and namespace | `urls.py` |
| JSON API endpoints, schemas, auth decorator | `api/` package |
| Incoming webhooks, providers, event types | `webhooks/` package |
| Outgoing third-party API calls | `rg "aiohttp\|ClientSession"` |
| Background tasks | `tasks.py` (`@task`) |
| Management commands and cron jobs | `management/commands/`, `helm/` cron values |
| Signals | `signals.py`, `@receiver` |
| Settings and env vars the app reads | `rg "settings\.[A-Z_]+"` in the app; `env(` in `config/settings.py` |
| Personal data and erasure | `gdpr.py`, PII fields (see `docs/gdpr.md`) |

Across the project, build the app map: which app imports from which (`rg "from
<package_name>\.<app>"`).

## 3. Reconcile (update runs only)

For every existing project doc in scope:

1. **Stale references** — every path and symbol mentioned must still exist
   (`rg -w <Symbol>`). Collect those that don't.
2. **Undocumented items** — models, endpoints, webhooks, tasks, commands, rules, or
   whole apps found in step 2 but missing from the docs.
3. **Removed items** — documented items with no counterpart in the code.
4. **Conflicts** — authored statements the code now contradicts (e.g. a rule says
   "only admins can delete" but the `rules.py` predicate allows members). Do **not**
   resolve these yourself.

## 4. Ask the user

The code cannot say *why*. Ask for what only the user knows:

- What the project/app is for, and who uses it.
- Meaning of domain terms and status values.
- Why each business rule exists; what happens at the edges.
- Decisions that look odd in the code, and anything planned to change.
- For each conflict from step 3: which is right — the doc or the code?

Rules:

- **One question at a time.** Wait for the answer before asking the next.
- On update runs, ask **only** about new, changed, or conflicting items — never
  repeat questions already answered in the docs.
- The user may answer "skip". Write `_TODO: <what is missing>_` in that place so the
  gap is visible and the next run asks again.
- Never invent rationale, history, or business context. Unknown is `_TODO_`, not a
  plausible guess.

## 5. Present the plan

Before writing anything, summarise the changes per file:

```
PROJECT DOCS
============

docs/this-project.md (update)
  + Apps: add `invoices` row
  ~ Integrations: Acme webhook now handles `invoice.refunded`
  ? Conflict: Key decisions says "no refunds after 30 days" — resolved by user: code is right

my_package/billing/README.md (update)
  + API: POST /api/v1/invoices/ (token auth, InvoiceIn -> InvoiceOut)
  - Reference: `billing/tasks.py::send_reminder` no longer exists
  ~ Business rules: "Invoice total is immutable once sent" — enforced in `Invoice.save`

my_package/invoices/README.md (create)
  2 TODOs: purpose of `Invoice.Status.DISPUTED`; who can void an invoice
```

Then ask:

> Should I write these changes?

Do not create or edit any file until the user confirms.

## 6. Write

Apply only the confirmed changes.

Writing rules:

- **Reference, don't copy.** Name files and symbols (`billing/models.py::Invoice`,
  `billing/rules.py::can_void_invoice`). No line numbers — they drift. No pasted
  code beyond a one-line signature.
- **Do not restate what the code shows.** No field-by-field model listings, no full URL
  dumps. Describe meaning and constraints; link to the code for detail.
- **API endpoints**: method, path, auth, and the Pydantic schema class names — not
  hand-written JSON schemas. The schemas are the source of truth.
- **Do not document generic patterns.** Link to the relevant `docs/*.md` page instead
  (e.g. "Token auth — see `docs/building-apis.md#authentication`").
- **No secrets or real data.** Setting *names* only, never values; no customer data
  in examples.
- Keep each app README short — aim for under ~150 lines. If an app needs more, that
  is a sign it may be doing too much; mention it to the user.
- Keep the `## Contents` list in `docs/this-project.md` in sync with its headings.
- Remove the `<!-- dj-doc: stub -->` marker once the overview has real content.

## 7. Finish

Report which files were created or updated and list the remaining `_TODO_` items so
the user can fill them in later or answer them on the next run.

This is a documentation-only change: do not run the test suite.
