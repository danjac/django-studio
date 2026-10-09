---
description: Run every audit in one sweep and combine the findings into one report
---

Run the project's audits in one sweep, report all findings together, then offer
fixes one audit at a time.

## 1. Warn and choose

Tell the user:

> A full audit runs up to seven audits. Each one reads most of the codebase, so
> the sweep takes a long time and uses a lot of tokens, more on a larger project.
> To check one area, run that audit on its own instead (e.g. `/djs-secure`).

Then read `docs/this-project.md`, list the audits, and ask which to run. Suggest
leaving out any audit the project makes pointless, with the reason: for example
`djs-seo` when the site has no public pages (an internal tool or a login-only
app). Default: all the audits you did not suggest leaving out.

| Audit | Checks |
| ----- | ------ |
| `djs-secure` | Settings, views, XSS, CSRF, IDOR, SQL injection |
| `djs-perf` | N+1 queries, missing indexes, caching, async |
| `djs-gdpr` | PII in models, erasure, consent, logging |
| `djs-a11y` | WCAG 2.1 AA: forms, icons, HTMX, Alpine, semantic HTML |
| `djs-seo` | robots.txt, meta tags, HTMX crawlability, sitemaps |
| `djs-deadcode` | Unused Python code, templates, static files, dependencies |
| `djs-remove-slop` | Django anti-patterns |

`/djs-full-coverage` is not part of the sweep: it writes tests rather than
auditing.

## 2. Run the audits

Run each selected audit by reading `.agents/skills/<name>/SKILL.md` and following
it up to and including its report, with these changes:

- Make no changes to any file. Where an audit installs a package (`djs-a11y`
  §9), report that it is missing instead.
- Stop after the report. Skip the audit's offer to fix and its approval step.
- For `djs-deadcode` and `djs-remove-slop`, the report is the proposed list of
  removals or fixes.

If you can start subagents, start one per audit, all at once, and give each these
instructions plus the audit's name; each returns its report unchanged. Otherwise
run the audits one after another in the order of the table.

## 3. Combined report

Group the findings across all audits, keeping each audit's own severity label and
tagging each finding with its audit:

```
FIX FIRST (CRITICAL, VIOLATION, REQUIRED):
  [secure] CRITICAL  orders/views.py:42 — OrderDetailView has no ownership check (IDOR)
  [a11y]   VIOLATION templates/orders/form.html:12 — input without a label
  [gdpr]   REQUIRED  User.phone has no anonymisation coverage

REVIEW (WARNING):
  [perf]   WARNING   orders/views.py:18 — count computed in Python
  ...

ADVISORY:
  [seo]    ADVISORY  no sitemap for public order pages
  ...

CLEANUP (djs-deadcode, djs-remove-slop):
  [deadcode] accounts/utils.py: format_initials() — no references found
  [slop]     orders/forms.py:9 — fields = "__all__"
  ...
```

Keep each audit's "uncertain" or "flagged only" notes with the finding. End with a
one-line count per audit, and name any audit that found nothing.

## 4. Offer fixes

Ask which audit's findings to fix first, suggesting the audit with the most
FIX FIRST findings, security first on a tie. Fix one audit at a time: go back to
its `SKILL.md` and follow its fix or approval step, which waits for the user's
confirmation. When that audit's fixes are done, offer the next one.
