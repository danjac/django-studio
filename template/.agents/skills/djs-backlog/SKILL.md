---
description: Keep the backlog and changelog current, pick up the next item, release
---

Keep this project's work queue in `docs/backlog.md` and its changelog in
`CHANGELOG.md`, pick up the next piece of work, and cut releases. The formats are in
`references/backlog-format.md` and `references/changelog-format.md`; read both
before writing either file.

Arguments: `$ARGUMENTS`

| Arguments | Section |
| --------- | ------- |
| _(none)_ | [Create](#1-create) if either file is missing, otherwise [Housekeeping](#2-housekeeping) |
| `add <description>` | [Add](#3-add) |
| `next [<slug>]` | [Next](#4-next) |
| `release [<version>]` | [Release](#5-release) |

## GitHub

Several steps use GitHub when the project has a remote there. Check once:

```bash
git remote get-url origin 2>/dev/null | grep -q github.com && gh auth status >/dev/null 2>&1 && echo github
```

If this doesn't print `github`, skip every GitHub step below and say so once.
Opening issues and PRs, and pushing, are visible to others: ask before the first
one in a run, unless the user has already approved that step.

## 1. Create

Create whichever of the two files is missing. Don't overwrite an existing one.

**`CHANGELOG.md`**: the intro and an empty `## Unreleased` section, as
`references/changelog-format.md` shows.

**`docs/backlog.md`**: read `docs/this-project.md` and the code, then propose items:

- **Features**: planned features from Key Decisions (public API, webhooks,
  background tasks, scheduled jobs), each with its doc or skill; core entities
  from the Glossary that have no app, model or CRUD views yet.
- **Chores**: `_TODO_` gaps in the overview (Key Flows especially), UI languages
  not yet translated, and the path to production: E2E tests for the key flows,
  `/djs-secure`, `/djs-a11y`, `/djs-perf`, `/djs-full-coverage`, `/djs-deploy`.
  Add blockers where order matters: E2E tests are blocked by the features they
  exercise, `/djs-full-coverage` and `/djs-deploy` by the features planned for
  launch.
- **Bugs**: open GitHub issues labelled `bug`, if any (with `(#N)`); otherwise
  `_None._`.
- Leave out anything the code shows is already done.

With a GitHub remote, also list open issues that no item covers and propose an item
for each, with its `(#N)`.

Show the proposed backlog and wait for the user to approve or change it. Then write
the file, and continue with [Next](#4-next) step 1 to suggest the first item.

## 2. Housekeeping

Read `docs/backlog.md`, `CHANGELOG.md` and `docs/this-project.md`. Collect the
changes below, show them as one list grouped by kind, and wait for approval.
Apply only what the user approves.

1. **Finished items**: move an item to Done when its PR merged, its issue is
   closed, or the code shows the work is done (e.g. the app, model or views it
   names exist). Check GitHub with:

   ```bash
   gh issue view <N> --json state,closedByPullRequestsReferences
   gh pr list --state merged --head <slug> --json number
   ```

   The first works for items with an issue; the second finds a PR opened by
   [Next](#4-next), whose branch is named after the slug.

   Record the PR number on the Done line. Without GitHub, use the code and
   `git log --oneline`.
2. **Issues not in the backlog**: open GitHub issues that no item links to.
   Propose an item for each, with its section, slug and `(#N)`.
3. **Broken links**: `(#N)` links to issues that don't exist.
4. **Blockers**: `Blocked by:` slugs that no item has, and blocker cycles.
5. **Stale items**: items that contradict `docs/this-project.md` (e.g. a feature
   Key Decisions now says is not needed), or that name apps, models or skills
   that no longer exist.
6. **Missing changelog entries**: user-visible changes merged since the newest
   `CHANGELOG.md` entry that have no entry. List merged PRs with
   `gh pr list --state merged --json number,title,mergedAt`, or commits with
   `git log --oneline` without GitHub. Propose an entry for each user-visible one;
   leave out tests, refactors, CI and developer docs.

Then ask whether to add, drop, reword or reorder anything, and apply the answers.
Commit the changes to `docs/backlog.md` and `CHANGELOG.md` together:

```bash
git add docs/backlog.md CHANGELOG.md
git commit -m "docs: update backlog and changelog"
```

Finish with [Next](#4-next) step 1 to suggest the next item.

## 3. Add

Turn the description into an item: pick the section, a slug, the skill or doc
that does the work, and any blockers (items it needs done first). If it names a
GitHub issue (`#N` or a URL), link it with `(#N)`.

Show the item and where it goes in its section, and wait for approval. Then write
it and commit:

```bash
git add docs/backlog.md
git commit -m "docs: add <slug> to backlog"
```

## 4. Next

### Step 1: suggest

With a slug, check that item. Without one, take the first unblocked item: the
first in Bugs, then Features, then Chores, skipping any item with a blocker
outside Done.

Show the item, why it is next, and any blocked items skipped, with their
unfinished blockers. If a named item is blocked, say which blockers are unfinished
and suggest the first unblocked item instead. **Wait for approval before doing
anything else.**

### Step 2: do the work

Start from an up-to-date default branch with a clean working tree. If there are
uncommitted changes, stop and ask.

1. With GitHub, open an issue for the item unless it has one, and add `(#N)` to
   its line:

   ```bash
   gh issue create --title "<description>" --body "<what done means; skill or doc to follow>"
   ```

2. Create a branch named after the slug:

   ```bash
   git checkout -b <slug>
   ```

3. Do the work. If the item names a skill, read `.agents/skills/<name>/SKILL.md`
   and follow it. If it names a doc, read it and follow `AGENTS.md`. Otherwise
   follow `AGENTS.md` for the task type.
4. If the change is user-visible, add a `CHANGELOG.md` entry under `Unreleased`:
   usually **Fixed** for a bug, **Added** for a feature. Most chores need none.
5. Move the item to Done in `docs/backlog.md`. Add the PR number once the PR
   exists.
6. Run `just check-all`. If it fails, fix what this work changed and run it
   again. If it still fails, stop and report without committing.
7. Commit on the branch. With GitHub, ask before pushing, then push and open a
   PR that closes the issue:

   ```bash
   git push -u origin <slug>
   gh pr create --title "<description>" --body "Closes #<N>"
   ```

   Add the PR number to the Done line, and the changelog entry if it has none,
   and commit and push that. Without GitHub, leave the branch for the user to
   merge.

Report what was done, the branch, and the issue and PR links.

## 5. Release

1. Run housekeeping check 6 (missing changelog entries) and offer to add any
   missing entries first.
2. Stop if `## Unreleased` has no entries, if the working tree has uncommitted
   changes, or if the current branch isn't the default branch. With GitHub, the
   default branch is `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`;
   without it, `main` or `master`, whichever exists.
3. Choose the version: the argument if given, otherwise today's date as
   `date +%y.%V.%u`. If a section for that version already exists, stop and ask
   for another version.
4. Show the version and the entries to be released, and **wait for approval**.
5. Rename `## Unreleased` to `## <version> - <YYYY-MM-DD>`, add a new empty
   `## Unreleased` above it, and commit:

   ```bash
   git add CHANGELOG.md
   git commit -m "chore: release <version>"
   ```

6. Tag the commit. Use `v<version>` for a version like `1.2.0`, and the version
   as it is for a date version:

   ```bash
   git tag -a <tag> -m "Release <version>"
   ```

7. With GitHub, ask before pushing. Then push the commit and the tag and create
   the release with the released section as its notes:

   ```bash
   git push origin HEAD <tag>
   gh release create <tag> --title "<version>" --notes-file <file with the section>
   ```

   Without GitHub, keep the tag local.

Releasing doesn't deploy. End by saying how to deploy the release: `/djs-deploy`
for a first deploy, otherwise the project's usual deploy (see
`docs/deployment.md`).
