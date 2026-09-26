# Changelog format

`CHANGELOG.md` at the project root records the user-visible changes to this
project, for the people who use and run it. The template doesn't ship it:
`/djs-kickoff` or `/djs-backlog` creates it.

It is not the django-studio template changelog that `/djs-sync` shows. Never copy
entries from that one into this file.

## Layout

```markdown
# Changelog

User-visible changes to this project. Newest first.

## Unreleased

### Fixed

- Searching with an empty query no longer fails. (#14)

## 26.39.6 - 2026-09-26

### Added

- Browse and search the product catalog. (#9)
```

A new file has the intro and an empty `## Unreleased` section.

## Entries

- New entries go under `## Unreleased`, below one of these headings, in this
  order: `Added`, `Changed`, `Deprecated`, `Fixed`, `Removed`. Add a heading only
  when it has entries.
- One bullet per change, written for a user of the site: what they can now do or
  what behaves differently, not which files changed.
- End the bullet with the issue or PR number when there is one: `(#14)`.
- Only user-visible changes earn an entry. Tests, refactors, CI and docs for
  developers don't.

## Releases

`/djs-backlog release` renames `## Unreleased` to `## <version> - <YYYY-MM-DD>` and
adds a new empty `## Unreleased` above it. Released sections are not edited
afterwards.
