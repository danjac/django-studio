**/djs-full-audit**

Runs the project's audits in one sweep: security, performance, GDPR,
accessibility, SEO, dead code and anti-patterns.

Asks which audits to run, suggesting which to leave out for this project (e.g.
SEO when there are no public pages), then runs them without changing any
file, in parallel where the agent supports subagents. Combines the findings into
one report grouped as FIX FIRST, REVIEW, ADVISORY and CLEANUP, then offers to fix
them one audit at a time.

A full sweep takes a long time and uses a lot of tokens. To check one area, run
that audit on its own (e.g. `/djs-secure`).

Example:
  /djs-full-audit
