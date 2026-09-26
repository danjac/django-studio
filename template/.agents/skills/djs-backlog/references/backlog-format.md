# Backlog format

`docs/backlog.md` is the project's ordered work queue. The template doesn't ship it:
`/djs-kickoff` or `/djs-backlog` creates it, so `/djs-sync` never touches it.

## Layout

```markdown
# Backlog

Work queue for this project, in order within each section. `/djs-backlog next`
picks up the first unblocked item: Bugs, then Features, then Chores.

## Bugs

- [ ] **search-empty-500**: Searching with an empty query returns a 500. (#14)

## Features

- [ ] **product-catalog**: Browse and search products. `/djs-create-crud catalog Product`
- [ ] **shopping-cart**: Add products to a cart and check out.
  Blocked by: product-catalog

## Chores

- [ ] **e2e-checkout**: E2E tests for checkout. `/djs-create-e2e`
  Blocked by: shopping-cart

## Done

- [x] **user-profile**: Display name and avatar on the user model. (#4, PR #7)
```

Keep all four headings, even when a section is empty; write `_None._` under an
empty one.

## Items

One list item per piece of work:

- **Slug** in bold: lower-kebab-case, unique across the file, never reused or
  renamed once another item names it. Blockers refer to items by slug.
- **Description**: one line saying what is done when the item is done.
- **Skill or doc** that does the work, in backticks, where one exists
  (`/djs-create-crud recipes Recipe`, `docs/webhooks.md`).
- **GitHub issue**: `(#N)` at the end of the line whenever the item has an issue,
  however it got one. No `(#N)` means no issue yet.
- **Blockers**: an indented `Blocked by: <slug>, <slug>` line. An item is blocked
  while any of its blockers is outside Done.

The sections:

| Section | For |
| ------- | --- |
| Bugs | Behaviour that is wrong now |
| Features | New behaviour users will see |
| Chores | Work users don't see: tests, audits, docs, deployment, upgrades |
| Done | Finished items, newest first |

Order within a section is priority order: the first item is the next one to do.

## Done

When an item is finished, tick it and move it to the top of Done, keeping its slug
and issue and adding the PR: `(#12, PR #15)`, or `(PR #15)` without an issue. Don't
delete Done items: blockers that name them must still resolve.
