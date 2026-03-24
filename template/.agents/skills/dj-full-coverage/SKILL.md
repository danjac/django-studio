---
description: Enable 100% coverage gate and write tests for all uncovered lines
---

Enforce 100% test coverage by enabling the coverage gate and writing tests
for every uncovered line.

---

## Warning

Before doing anything else, display this message and wait for explicit
confirmation:

> **100% test coverage is a late-stage goal.**
> Enforcing it early slows development: every new feature requires tests
> before the implementation can land, and exploratory code becomes painful
> to write. It is best applied once the project is at or close to feature
> complete.
>
> **Tip:** Run `/dj-deadcode` first to remove any unused code you
> don't need. There is no point writing tests for dead code.
>
> Do you want to proceed?

Stop if the user does not confirm.

---

## Step 1 — Enable the coverage gate

Open `pyproject.toml` and look for `--cov-fail-under=100` in the
`[tool.pytest.ini_options]` `addopts` list.

- **If the line is present but commented out** (e.g. `# "--cov-fail-under=100",`),
  uncomment it.
- **If the line is absent**, add `"--cov-fail-under=100",` to `addopts`,
  after the `"--no-cov-on-fail",` entry.

---

## Step 2 — Identify uncovered lines

Coverage applies to **unit tests only** (`just test`). E2E tests (`just test-e2e`) are
not part of this workflow — they exist to cover specific user interactions, not to
drive line coverage.

Run the unit test suite to get the current coverage report:

```bash
just test 2>&1 | tail -40
```

Parse the `term-missing` output. For each file with missing lines, note the
exact line numbers. Read the source file for each gap before writing any
tests — understand what the code does before deciding how to test it.

---

## Step 3 — Write tests to cover the gaps

Work through each uncovered file. For each gap:

1. Read the source lines to understand the code path.
2. Find or create the appropriate test file (`<package_name>/<app_name>/tests/test_*.py`).
3. Add the minimum test(s) needed to exercise the uncovered lines.

**Rules** (see `docs/Testing.md` for full conventions):
- Test behaviour, not implementation. A test that only exists to tick a
  coverage box and asserts nothing meaningful is worse than no test.
- Do not mock private methods. Mock at system boundaries (HTTP, filesystem,
  external APIs) using `aioresponses`, `pytest-mock`, or `unittest.mock`.
  See `docs/Testing.md` — Mocking section.
- One logical scenario per test function.
- Use existing factories and fixtures from `conftest.py` and
  `tests/fixtures.py` before creating new ones.

After adding tests for each file, re-run to confirm the gap is closed:

```bash
just test 2>&1 | tail -40
```

---

## Step 4 — Verify full coverage

Once all gaps are addressed, run the full suite:

```bash
just check-all
```

If coverage is still below 100%, go back to Step 2 and repeat. Do not stop
until `just check-all` exits 0 with no coverage failures.
