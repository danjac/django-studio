**/djs-backlog [add <description> | next [<slug>] | release [<version>]]**

Keeps the project's work queue in `docs/backlog.md` and its changelog in
`CHANGELOG.md`, picks up the next piece of work, and cuts releases.

The backlog has four sections: Bugs, Features, Chores and Done. Each item has a
slug, the skill or doc that does the work, its GitHub issue as `(#N)` once it has
one, and any blockers (`Blocked by: <slug>`). `/djs-kickoff` writes the first
backlog.

Usage:

- `/djs-backlog`: creates `docs/backlog.md` and `CHANGELOG.md` if either is missing.
  Otherwise tidies up: moves finished items to Done, offers to add open GitHub
  issues, flags broken blockers and stale items, and adds missing changelog
  entries. Every change is shown for approval first.
- `/djs-backlog add <description>`: adds an item, with its section, slug and
  blockers, after you approve it.
- `/djs-backlog next [<slug>]`: suggests the first unblocked item (Bugs, then
  Features, then Chores), or checks the one you name, and waits for approval. Then
  it opens a GitHub issue if needed, creates a branch, does the work, adds a
  changelog entry, runs `just check-all` and opens a PR that closes the issue.
- `/djs-backlog release [<version>]`: turns `Unreleased` in `CHANGELOG.md` into a
  release section (default version: today's date), tags it and creates a GitHub
  release. It doesn't deploy.

Pushing, and opening issues, PRs and releases, happen only after you approve them.
Without a GitHub remote, the skill works on the files and local branches only.

Examples:
  /djs-backlog
  /djs-backlog add "Searching with an empty query returns a 500"
  /djs-backlog next
  /djs-backlog next shopping-cart
  /djs-backlog release 1.0.0
