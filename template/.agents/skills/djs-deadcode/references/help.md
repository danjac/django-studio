**/djs-deadcode**

Scans the project for unused code and assets.

Uses `vulture` for Python dead code detection, checks for unreferenced URL
patterns, templates, and static files, and uses `deptry` for unused
dependencies. It checks each dependency for references from settings,
templates, scripts and backend URLs before proposing removal. Always presents
a consolidated summary for explicit approval before making any changes.

Example:
  /djs-deadcode
