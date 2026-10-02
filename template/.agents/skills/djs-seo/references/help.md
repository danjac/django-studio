**/djs-seo**

Audits the codebase for search engine optimisation gaps on public pages.

Lists the pages an anonymous visitor can reach, then checks robots.txt and robots
directives (`noindex`, `nofollow`, `noarchive`), titles and meta descriptions,
HTMX-loaded content, status codes, canonical and Open Graph tags, sitemaps and
structured data. Projects with no public content get a short report.
Reports VIOLATION, WARNING, and ADVISORY findings. Read `docs/seo.md` for
conventions used in this project.

Example:
  /djs-seo
