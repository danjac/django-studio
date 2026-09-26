---
description: Keep the backlog and changelog current, pick up the next item, release
---

Keep this project's work queue (bugs, features and chores, with blockers) and its
changelog in `CHANGELOG.md`, pick up the next piece of work, and cut releases. The
formats are in `references/backlog-format.md` and
`references/changelog-format.md`; read both before changing either.

Arguments: `$ARGUMENTS`

| Arguments | Section |
| --------- | ------- |
| _(none)_ | [Create](#1-create) if `CHANGELOG.md` or the backlog is missing, otherwise [Housekeeping](#2-housekeeping) |
| `add <description>` | [Add](#3-add) |
| `next [<issue or slug>]` | [Next](#4-next) |
| `release [<version>]` | [Release](#5-release) |

## Where the backlog lives

Check once whether the project has a GitHub remote:

```bash
git remote get-url origin 2>/dev/null | grep -q github.com && gh auth status >/dev/null 2>&1 && echo github
```

If it prints `github`, GitHub issues are the backlog (**GitHub mode**). Otherwise
`docs/backlog.md` is (**file mode**): skip every GitHub step below and say so once.

In GitHub mode, the backlog is missing when the repository has no issues at all
(`gh issue list --state all --limit 1` prints nothing) and there is no
`docs/backlog.md`. In file mode, it is missing when `docs/backlog.md` is.

Creating labels and issues, opening PRs, and pushing are visible to others: ask
before the first one in a run, unless the user has already approved that step.

## 1. Create

Create whichever is missing. Don't overwrite an existing `CHANGELOG.md`, and
don't add to an existing backlog.

**`CHANGELOG.md`**: the intro and an empty `## Unreleased` section, as
`references/changelog-format.md` shows.

**Backlog**: read `docs/this-project.md` and the code, then propose items:

- **Features**: planned features from Key Decisions (public API, webhooks,
  background tasks, scheduled jobs), each with its doc or skill; core entities
  from the Glossary that have no app, model or CRUD views yet.
- **Chores**: `_TODO_` gaps in the overview (Key Flows especially), UI languages
  not yet translated, and the path to production: E2E tests for the key flows,
  `/djs-secure`, `/djs-a11y`, `/djs-perf`, `/djs-full-coverage`, `/djs-deploy`.
  Add blockers where order matters: E2E tests are blocked by the features they
  exercise, `/djs-full-coverage` and `/djs-deploy` by the features planned for
  launch.
- **Bugs**: none, unless the user names some.
- Leave out anything the code shows is already done.

Show the proposed backlog in order, with each item's type, priority and blockers,
and wait for the user to approve or change it. Then:

- **GitHub mode**: create the missing labels, then the issues in the approved
  order, then their blockers, as in "Moving to GitHub issues" in
  `references/backlog-format.md`.
- **File mode**: write `docs/backlog.md`.

Commit whichever of `CHANGELOG.md` and `docs/backlog.md` this step created:

```bash
git add <files>
git commit -m "docs: add backlog and changelog"
```

Continue with [Next](#4-next) step 1 to suggest the first item.

## 2. Housekeeping

Read `CHANGELOG.md`, `docs/this-project.md` and the backlog. Collect the changes
below, show them as one list grouped by kind, and wait for approval. Apply only
what the user approves.

**GitHub mode:**

1. **Backlog file**: if `docs/backlog.md` exists, propose moving its open items to
   issues and deleting it, as in "Moving to GitHub issues" in
   `references/backlog-format.md`. Show the issues it would create.
2. **Labels**: open issues without a type label (`bug`, `enhancement`, `chore`).
   Propose one for each, and a priority where the issue says it is urgent or can
   wait.
3. **Blockers**: blocker cycles, and issues blocked by an issue closed as not
   planned.
4. **Finished issues**: open issues whose work the code shows is done (e.g. the
   app, model or views they name exist). Propose closing each with a comment
   saying where the work is.
5. **Stale issues**: open issues that contradict `docs/this-project.md` (e.g. a
   feature Key Decisions now says is not needed), or that name apps, models or
   skills that no longer exist.

**File mode:**

1. **Finished items**: move an item to Done when the code shows the work is done,
   or `git log --oneline` shows a merged branch named after its slug.
2. **Blockers**: `Blocked by:` slugs that no item has, and blocker cycles.
3. **Stale items**: as in GitHub mode.

**Both modes:**

- **Missing changelog entries**: user-visible changes merged since the newest
  `CHANGELOG.md` entry that have no entry. List merged PRs with
  `gh pr list --state merged --json number,title,mergedAt`, or commits with
  `git log --oneline` in file mode. Propose an entry for each user-visible one;
  leave out tests, refactors, CI and developer docs.

Then ask whether to add, drop, reword or reprioritise anything, and apply the
answers. Commit the changes to `CHANGELOG.md` and `docs/backlog.md` (including
its deletion) together, if there are any:

```bash
git add -A <files>
git commit -m "docs: update backlog and changelog"
```

Finish with [Next](#4-next) step 1 to suggest the next item.

## 3. Add

Turn the description into an item: its type (bug, feature or chore), the skill or
doc that does the work, and any blockers (items it needs done first). In GitHub
mode, also pick its priority; in file mode, a slug and its place in the section.

Show the item and wait for approval. Then:

- **GitHub mode**: create the issue, with `--label "priority: high"` or
  `--label "priority: low"` if it has one, and `--blocked-by` if it has blockers.
  If the description names an existing issue (`#N` or a URL), label it and add
  its blockers with `gh issue edit` instead.

  ```bash
  gh issue create --title "<description>" --body "<what done means; skill or doc to follow>" --label <type>
  ```

- **File mode**: write the item into `docs/backlog.md` and commit:

  ```bash
  git add docs/backlog.md
  git commit -m "docs: add <slug> to backlog"
  ```

## 4. Next

### Step 1: suggest

With an argument, check that issue (GitHub mode) or item (file mode). Without
one, take the first unblocked item in the order `references/backlog-format.md`
gives for the mode.

Show the item, why it is next, and any higher items skipped because they are
blocked, with their unfinished blockers. If a named item is blocked, say which
blockers are unfinished and suggest the first unblocked item instead. **Wait for
approval before doing anything else.**

### Step 2: do the work

Start from an up-to-date default branch with a clean working tree. If there are
uncommitted changes, stop and ask.

1. Create a branch: `<N>-<short-kebab-title>` for issue `#N` (e.g.
   `14-search-empty-500`), or the slug in file mode.

   ```bash
   git checkout -b <branch>
   ```

2. Do the work. If the item names a skill, read `.agents/skills/<name>/SKILL.md`
   and follow it. If it names a doc, read it and follow `AGENTS.md`. Otherwise
   follow `AGENTS.md` for the task type.
3. If the change is user-visible, add a `CHANGELOG.md` entry under `Unreleased`,
   ending with `(#N)` in GitHub mode: usually **Fixed** for a bug, **Added** for a
   feature. Most chores need none.
4. In file mode, move the item to Done in `docs/backlog.md`.
5. Run `just check-all`. If it fails, fix what this work changed and run it
   again. If it still fails, stop and report without committing.
6. Commit on the branch. In GitHub mode, ask before pushing, then push and open a
   PR that closes the issue:

   ```bash
   git push -u origin <branch>
   gh pr create --title "<issue title>" --body "Closes #<N>"
   ```

   Merging the PR closes the issue, which unblocks the issues it blocks. In file
   mode, leave the branch for the user to merge.

Report what was done, the branch, and the issue and PR links.

## 5. Release

1. Run the housekeeping check for missing changelog entries and offer to add any
   missing entries first.
2. Stop if `## Unreleased` has no entries, if the working tree has uncommitted
   changes, or if the current branch isn't the default branch. In GitHub mode, the
   default branch is `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`;
   in file mode, `main` or `master`, whichever exists.
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

7. In GitHub mode, ask before pushing. Then push the commit and the tag and create
   the release with the released section as its notes:

   ```bash
   git push origin HEAD <tag>
   gh release create <tag> --title "<version>" --notes-file <file with the section>
   ```

   In file mode, keep the tag local.

Releasing doesn't deploy. End by saying how to deploy the release: `/djs-deploy`
for a first deploy, otherwise the project's usual deploy (see
`docs/deployment.md`).
