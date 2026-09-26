**/djs-backlog [add <description> | next [<issue or slug>] | release [<version>]]**

Keeps the project's work queue and its changelog in `CHANGELOG.md`, picks up the
next piece of work, and cuts releases.

With a GitHub remote, GitHub issues are the backlog: a `bug`, `enhancement` or
`chore` label for the type, an optional `priority: high` or `priority: low` label,
and GitHub's "blocked by" relationships. Merging a PR that says `Closes #N`
finishes an item. Without a remote, the backlog is `docs/backlog.md`, with Bugs,
Features, Chores and Done sections and `Blocked by: <slug>` lines. `/djs-kickoff`
writes the first backlog.

Usage:

- `/djs-backlog`: creates the backlog and `CHANGELOG.md` if either is missing.
  Otherwise tidies up: moves `docs/backlog.md` to issues once the project has a
  GitHub remote, labels unlabelled issues, flags blocker cycles, finished and
  stale items, and adds missing changelog entries. Every change is shown for
  approval first.
- `/djs-backlog add <description>`: adds an item, with its type, priority and
  blockers, after you approve it.
- `/djs-backlog next [<issue or slug>]`: suggests the first unblocked item
  (by priority, then bugs, features and chores, oldest first), or checks the one
  you name, and waits for approval. Then it creates a branch, does the work, adds
  a changelog entry, runs `just check-all` and opens a PR that closes the issue.
- `/djs-backlog release [<version>]`: turns `Unreleased` in `CHANGELOG.md` into a
  release section (default version: today's date), tags it and creates a GitHub
  release. It doesn't deploy.

Pushing, and creating labels, issues, PRs and releases, happen only after you
approve them. Without a GitHub remote, the skill works on the files and local
branches only.

Examples:
  /djs-backlog
  /djs-backlog add "Searching with an empty query returns a 500"
  /djs-backlog next
  /djs-backlog next 14
  /djs-backlog next shopping-cart
  /djs-backlog release 1.0.0
