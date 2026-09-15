<!-- dj-doc: stub -->
# This Project

This page describes **this project specifically** — what it does, who it is for, and
how its apps fit together. The other pages in `docs/` describe the generic stack and
conventions and are maintained by the template.

Each app has its own `README.md` next to its code with business rules, lifecycles,
APIs and integrations. This page is the map; the app READMEs are the detail.

> **Stub.** Run `/dj-doc` to fill this in: it reads the code, asks you for the
> context the code cannot provide, and keeps this page and the app READMEs up to
> date on later runs. You can also edit it by hand — keep the headings.

## Contents

- [Purpose](#purpose)
- [Users and Roles](#users-and-roles)
- [Glossary](#glossary)
- [Apps](#apps)
- [Key Flows](#key-flows)
- [Integrations](#integrations)
- [Key Decisions](#key-decisions)

## Purpose

_What problem does this project solve, and for whom? What is deliberately out of
scope? Two or three sentences._

## Users and Roles

_Who uses the system and what each kind of user can do. Link to permissions in the
relevant app README rather than repeating them._

| Role | Description |
| ---- | ----------- |
| _e.g. Organisation admin_ | _Manages members and billing for an organisation_ |

## Glossary

_Domain terms used in code, UI and conversation, with their business meaning. Note
where the code name differs from what users call it._

- **_Term_** — _meaning_

## Apps

_One row per Django app under the project package. Keep responsibilities one line —
detail belongs in the app README._

| App | Responsibility | Depends on | Docs |
| --- | -------------- | ---------- | ---- |
| `users` | _User accounts and profiles_ | — | `my_package/users/README.md` |

## Key Flows

_The few end-to-end journeys that matter most (e.g. sign up → create organisation →
invite member), listing the apps involved in order._

## Integrations

_Third-party services the project calls or receives webhooks from. Generic patterns
are in `docs/integrating-apis.md` and `docs/webhooks.md`._

| Provider | Direction | Used for | App | Settings |
| -------- | --------- | -------- | --- | -------- |
| _e.g. Mailgun_ | _API out / webhook in_ | _Transactional email_ | _—_ | _`MAILGUN_API_KEY`_ |

## Key Decisions

_Significant choices and why they were made, newest first. Short entries — enough
that a newcomer (or an agent) does not undo them by accident._

| Date | Decision | Why |
| ---- | -------- | --- |
| _YYYY-MM-DD_ | _Decision_ | _Reason_ |
