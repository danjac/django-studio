**/dj-full-coverage**

Enables the 100% coverage gate and writes tests for every uncovered line.

Warns the user that enforcing 100% coverage is a late-stage concern and
waits for confirmation before making any changes. Once confirmed:

1. Uncomments or adds `--cov-fail-under=100` in `pyproject.toml`.
2. Runs `just test` (unit tests only — E2E tests are for user interactions, not coverage)
   to identify uncovered lines.
3. Adds or extends tests to cover every gap, following project conventions
   (behaviour-focused, no private-method mocking, existing fixtures first).
   See `docs/testing.md` for mocking rules.
4. Iterates with `just test` until coverage is 100%, then runs `just check-all` to verify.

Example:
  /dj-full-coverage
