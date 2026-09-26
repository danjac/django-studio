# Backlog: suggest the next unblocked item

Covers `/djs-backlog next`: the top Features item is blocked by a later one, so the
skill must skip it, suggest the first unblocked item, and stop for approval
without changing anything.

## Setup

```sh
cat > docs/backlog.md <<'EOF2'
# Backlog

Work queue for this project, in order within each section. `/djs-backlog next`
picks up the first unblocked item: Bugs, then Features, then Chores.

## Bugs

_None._

## Features

- [ ] **shopping-cart**: Add products to a cart and check out.
  Blocked by: product-catalog
- [ ] **product-catalog**: Browse and search products. `/djs-create-crud catalog Product`

## Chores

- [ ] **e2e-checkout**: E2E tests for checkout. `/djs-create-e2e`
  Blocked by: shopping-cart

## Done

_None._
EOF2
cat > CHANGELOG.md <<'EOF2'
# Changelog

User-visible changes to this project. Newest first.

## Unreleased
EOF2
```

## Prompt

```text
/djs-backlog next
```

## Check

```sh
grep -q "product-catalog" "$EVAL_BUILD_OUTPUT"
test "$(git rev-list --count eval-baseline..HEAD)" = 0
test -z "$(git status --porcelain)"
test "$(git branch --format='%(refname:short)' | wc -l)" = 1
```

## Review

```text
`/djs-backlog next` ran in this project, with no answers given, and produced this
output:

{build_output}

The backlog is `docs/backlog.md`. Verify these facts:

1. The output suggests `product-catalog` as the next item.
2. It says `shopping-cart` was skipped because `product-catalog` blocks it.
3. It asks for approval and does not claim to have started the work: no issue,
   branch, commit or code change.
```
