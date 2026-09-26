# Backlog format

The backlog is the project's ordered work queue of bugs, features and chores, with
blockers. Where it lives depends on the project:

- **With a GitHub remote**: GitHub issues are the backlog. Each open issue is an
  item; closing it (usually by merging a PR that says `Closes #N`) finishes it.
- **Without one**: `docs/backlog.md`. The template doesn't ship it: `/djs-kickoff` or
  `/djs-backlog` creates it, so `/djs-sync` never touches it.

Once a project has a GitHub remote, `/djs-backlog` moves the open items in
`docs/backlog.md` to issues and deletes the file.

## GitHub issues

### Labels

Every open issue has one type label:

| Label | For |
| ----- | --- |
| `bug` | Behaviour that is wrong now |
| `enhancement` | New behaviour users will see |
| `chore` | Work users don't see: tests, audits, docs, deployment, upgrades |

Priority is optional: `priority: high` or `priority: low`. An issue without either
has normal priority.

GitHub creates `bug` and `enhancement` in a new repository. Create any that are
missing:

```bash
gh label create chore --color c5def5 --description "Tests, audits, docs, deployment, upgrades"
gh label create "priority: high" --color d93f0b --description "Do before normal priority"
gh label create "priority: low" --color c2e0c6 --description "Do after normal priority"
```

### Issues

- **Title**: one line saying what is done when the issue is done.
- **Body**: what done means, and the skill or doc that does the work, in backticks,
  where one exists (`/djs-create-crud recipes Recipe`, `docs/webhooks.md`).
- **Blockers**: GitHub's "blocked by" relationships, set with
  `gh issue create --blocked-by <N>,<N>` or `gh issue edit <N> --add-blocked-by <N>`.
  An issue is blocked while any of its blockers is open.

### Order

The next issue is the first open, unblocked one in this order:

1. Priority: `priority: high`, then normal, then `priority: low`.
2. Type: `bug`, then `enhancement`, then `chore`.
3. Age: lowest issue number first.

List the open issues with their labels and blockers:

```bash
gh issue list --state open --limit 500 --json number,title,labels,blockedBy
```

`blockedBy.nodes` holds each blocker's `number` and `state`.

## `docs/backlog.md`

### Layout

```markdown
# Backlog

Work queue for this project, in order within each section. `/djs-backlog next`
picks up the first unblocked item: Bugs, then Features, then Chores.

## Bugs

- [ ] **search-empty-500**: Searching with an empty query returns a 500.

## Features

- [ ] **product-catalog**: Browse and search products. `/djs-create-crud catalog Product`
- [ ] **shopping-cart**: Add products to a cart and check out.
  Blocked by: product-catalog

## Chores

- [ ] **e2e-checkout**: E2E tests for checkout. `/djs-create-e2e`
  Blocked by: shopping-cart

## Done

- [x] **user-profile**: Display name and avatar on the user model.
```

Keep all four headings, even when a section is empty; write `_None._` under an
empty one.

### Items

One list item per piece of work:

- **Slug** in bold: lower-kebab-case, unique across the file, never reused or
  renamed once another item names it. Blockers refer to items by slug.
- **Description**: one line saying what is done when the item is done.
- **Skill or doc** that does the work, in backticks, where one exists
  (`/djs-create-crud recipes Recipe`, `docs/webhooks.md`).
- **Blockers**: an indented `Blocked by: <slug>, <slug>` line. An item is blocked
  while any of its blockers is outside Done.

The sections map to the GitHub labels:

| Section | Label |
| ------- | ----- |
| Bugs | `bug` |
| Features | `enhancement` |
| Chores | `chore` |
| Done | closed issues |

Order within a section is priority order: the first item is the next one to do.

### Done

When an item is finished, tick it and move it to the top of Done, keeping its slug.
Don't delete Done items: blockers that name them must still resolve.

### Moving to GitHub issues

1. For each open item, in file order so earlier items get lower numbers, create an
   issue with the section's label, the description as its title, and the skill or
   doc in its body. An item that ends with `(#N)` already has an issue: add the
   label to that one instead of creating another.
2. Once every item has an issue, add the blockers with
   `gh issue edit <N> --add-blocked-by <N>`, mapping each slug to its item's issue.
   Leave out blockers that are in Done, since they are finished.
3. Delete the file.
