**/dj-deadcode**

Scans the project for unused code and assets.

Uses `vulture` for Python dead code detection, checks for unreferenced URL
patterns, templates, and static files, and uses `deptry` for unused
dependencies. Always presents a consolidated summary for explicit approval
before making any changes.

Example:
  /dj-deadcode
