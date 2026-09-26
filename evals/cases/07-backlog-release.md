# Backlog: release the changelog

Covers `/djs-backlog release` in a project without a GitHub remote: `Unreleased`
becomes a versioned section under a new empty `Unreleased`, the commit is tagged,
and nothing is pushed.

## Setup

```sh
cat > docs/backlog.md <<'EOF2'
# Backlog

Work queue for this project, in order within each section. `/djs-backlog next`
picks up the first unblocked item: Bugs, then Features, then Chores.

## Bugs

_None._

## Features

_None._

## Chores

_None._

## Done

- [x] **search-empty-500**: Searching with an empty query returns a 500.
- [x] **product-catalog**: Browse and search products.
EOF2
cat > CHANGELOG.md <<'EOF2'
# Changelog

User-visible changes to this project. Newest first.

## Unreleased

### Added

- Browse and search the product catalog.

### Fixed

- Searching with an empty query no longer fails.
EOF2
```

## Prompt

```text
/djs-backlog release 1.0.0

Answers:

- Missing changelog entries: none to add; the entries under Unreleased are complete.
- Release: approved as shown.
```

## Check

```sh
test "$(grep '^## ' CHANGELOG.md | head -2 | tr '\n' '|')" = "## Unreleased|## 1.0.0 - $(date +%F)|"
test -z "$(sed -n '/^## Unreleased/,/^## 1.0.0/p' CHANGELOG.md | sed '1d;$d' | tr -d '[:space:]')"
sed -n '/^## 1.0.0/,$p' CHANGELOG.md | grep -q "Browse and search the product catalog."
sed -n '/^## 1.0.0/,$p' CHANGELOG.md | grep -q "Searching with an empty query no longer fails."
git tag --points-at HEAD | grep -qx v1.0.0
test "$(git rev-list --count eval-baseline..HEAD)" = 1
test -z "$(git status --porcelain)"
```

## Review

```text
Review a changelog release made with `/djs-backlog release 1.0.0` in this project.

Verify these facts about `CHANGELOG.md`:

1. It starts with the `# Changelog` heading and intro, then an empty
   `## Unreleased` section.
2. The `## 1.0.0 - <date>` section below it holds the Added and Fixed entries,
   with their headings, unchanged.
3. No other section or entry was added.
```
