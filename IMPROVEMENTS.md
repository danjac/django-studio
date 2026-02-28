## Improvements

Add improvements here.

~~## Document Pydantic for JSON serialization instead of DRF (2026-02-28)~~

~~Add a note to the template documentation (AGENTS.md or equivalent) stating that Pydantic should be used for JSON serialization and validation — both for third-party/external API responses and for internal APIs — instead of Django REST Framework serializers. When Pydantic is added, also include the following in `pyproject.toml` to prevent ruff from moving Pydantic base class imports into `TYPE_CHECKING` blocks:~~

**Resolved**: Added a "JSON Serialization and Validation" section to the generated project's `AGENTS.md` documenting Pydantic as the preferred approach over DRF, and including the ruff `flake8-type-checking` config snippet to add when Pydantic is installed.

~~## Rename justfile `e2e` command to `test-e2e` and update docs (2026-02-27)~~

~~Rename the `e2e` just recipe to `test-e2e` (and `e2e-headed` to `test-e2e-headed`) for consistency with the `test` command naming convention. Update AGENTS.md/CLAUDE.md documentation to reference `just test-e2e` and `just test-e2e-headed` accordingly.~~

**Resolved**: Renamed `e2e` → `test-e2e` and `e2e-headed` → `test-e2e-headed` in justfile; updated references in AGENTS.md, docs/Testing.md, and docs/Local-Development.md.
