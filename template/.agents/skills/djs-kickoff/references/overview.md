# Writing the project overview

How to turn the product interview into `docs/this-project.md`, the project's
permanent overview. `/djs-kickoff` uses it when the page is still the template stub,
and `/djs-bootstrap` uses it for a new project.

## Questions

Skip anything the user has already said, and ask the rest in one or two rounds,
not one question at a time:

- Purpose: what the project does and who it is for, in a line or two
- Core entities: the main things users create, browse or manage
- User roles, and what each can do
- Public site, or login required for most pages
- Languages the UI needs
- Whether it needs a public API, incoming webhooks, or background tasks (email,
  imports, scheduled jobs)

The user may skip any question. Stack choices are fixed by the template, so don't
ask about packages or frameworks.

## Writing the page

The template ships the page as a stub with guidance under each heading. Keep every
heading and fill in these sections, replacing their guidance and placeholder rows:

| Section | From the interview |
| ------- | ------------------ |
| Purpose | The purpose, plus any detail the user gave |
| Users and Roles | One table row per role, with what it can do |
| Glossary | One entry per core entity: what it is and who creates it |
| Key Decisions | One row each, dated today: public or login-only access, the UI languages (the first is the default), and the public API, incoming webhooks and background tasks, each as "planned" (with what for) or "not needed" |

Write `_TODO: <what is missing>_` for anything the user skipped. Under Key Flows,
replace the guidance with `_TODO: the main end-to-end journeys_`. Leave Apps and
Integrations as they are: `/djs-doc` fills them from the code.

Remove the `<!-- djs-doc: stub -->` line and the `> **Stub.**` note, so `/djs-doc`
treats the page as written and keeps these answers.
