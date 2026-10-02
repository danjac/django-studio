---
description: SEO audit: robots.txt, meta tags, sitemaps, HTMX crawlability
---

Audit the codebase for search engine optimisation gaps on public pages.

Read `docs/seo.md` first: it holds the conventions and fixes this audit checks
against.

Report findings in three groups: **VIOLATION** (a public page crawlers cannot index
correctly), **WARNING** (likely issue; needs manual verification), and **ADVISORY**
(improvement worth making if search traffic matters).

---

### 1. Scope: public pages

Read `config/urls.py`, every included `urls.py`, and the views they point at. List
every page an anonymous visitor can `GET` and receive HTML for. Leave out:

- views behind `@login_required`, `LoginRequiredMixin` or a permission check
- `account/`, `admin/`, `i18n/`, health checks and `.well-known/` URLs
- `robots.txt`, `manifest.json`, `favicon.*`, JSON endpoints and HTMX-only partials
- `privacy` and other legal pages (crawlable, but not search targets)

Read `docs/this-project.md` for who the users are and what is public. If it says
search traffic is out of scope, or the list above holds only `index` and `about`,
run sections 2, 4 and 6 only, and say in the report that the project has no public
content to optimise yet.

Print the list of public pages before the findings. Every later section checks only
these pages.

---

### 2. robots.txt

Read `views.robots` in `<package_name>/views.py`.

| Check | Severity if failing |
|---|---|
| Each public page's URL is covered by an `Allow:` line (exact path with `$`, or a prefix for model pages) | VIOLATION |
| `Disallow: /` is still the last rule, so new URLs stay hidden until allowed | WARNING |
| An `Allow:` line names a URL that requires login or no longer exists | WARNING |
| A sitemap is wired up but `robots.txt` has no absolute `Sitemap:` line, or does not allow the sitemap URL | VIOLATION |

---

### 3. Titles and meta tags

For each public page, read its template and the templates it extends.

| Check | Severity if failing |
|---|---|
| Template overrides `{% block title %}` with `{% title_tag ... %}` (pages other than `index`) | VIOLATION |
| Two public pages render the same title | WARNING |
| `META_TAGS` has a `description` that is still the template default (`META_DESCRIPTION`) | WARNING |
| A page generated from a model renders the shared site description instead of its own | WARNING |
| A public page renders no description while others set their own | WARNING |
| A template's `{% block meta %}` adds `<meta name="description">` while `META_TAGS` still has `description` (two description tags) | VIOLATION |
| A public page has a `noindex` meta tag but is meant to be found | VIOLATION |

Per-page descriptions go in `{% block meta %}` once `description` is removed from
`META_TAGS` (see `docs/seo.md#titles-and-descriptions`). Recommend that only when a
WARNING above applies.

---

### 4. HTMX and rendering

Scan public page templates for `hx-get`, `hx-trigger`, `hx-push-url` and `hx-boost`,
and the views that serve them.

| Check | Severity if failing |
|---|---|
| The page's main content loads through `hx-trigger="load"` or `revealed` instead of the first response | VIOLATION |
| A URL used in `hx-push-url` or a boosted link returns a partial on a direct `GET` (view or template does not fall back to `base.html`) | VIOLATION |
| `HtmxCacheMiddleware` is missing from `MIDDLEWARE` | VIOLATION |
| Public list pagination has `hx-get` without a matching `href` | WARNING |
| A public link is an element with `@click` or `hx-get` but no `href` | WARNING |

---

### 5. Status codes

Read the views for public pages.

| Check | Severity if failing |
|---|---|
| A public detail view looks up its object without `get_object_or_404` (or an equivalent `Http404`) and renders an empty page on a miss | VIOLATION |
| A URL was renamed and the old path redirects with `302` instead of `301` | WARNING |

---

### 6. Content structure

Accessibility checks overlap here; `/djs-a11y` covers heading order and `alt` text in
full. Check only what affects search results:

| Check | Severity if failing |
|---|---|
| A public page has no `<h1>`, or more than one | WARNING |
| `<img>` in public content with no `alt` | WARNING |
| Link text on public pages is generic ("click here", "read more") with no `aria-label` | ADVISORY |
| `<html lang>` is not set from `LANGUAGE_CODE` | WARNING |

---

### 7. Canonical URLs and social previews

| Check | Severity if failing |
|---|---|
| A public list page accepts sort, filter or `page` query parameters and has no `<link rel="canonical">` in `{% block meta %}` | WARNING |
| A public page generated from a model has no Open Graph tags (`og:title`, `og:description`, `og:url`) | ADVISORY |
| `og:image` or `canonical` uses a relative URL | VIOLATION |

---

### 8. Sitemaps

| Check | Severity if failing |
|---|---|
| Public pages generated from models exist and there is no sitemap | ADVISORY — say what each sitemap costs to maintain |
| A sitemap lists objects that are not public (drafts, private records, login-only views) | VIOLATION |
| A sitemap's model has no `get_absolute_url()` | VIOLATION |
| A sitemap exists but no test requests `sitemap.xml` | ADVISORY |

Do not recommend a sitemap when the only public pages are `index` and `about`.

---

### 9. Structured data and localisation

| Check | Severity if failing |
|---|---|
| A public model page maps clearly to a schema.org type (article, product, event, organisation) and has no JSON-LD | ADVISORY |
| JSON-LD is rendered with `\|safe` on unescaped `json.dumps` output | VIOLATION — XSS; use the `json_ld` tag in `docs/seo.md#structured-data` |
| `docs/this-project.md` says translated pages must rank in other languages, and public URLs are not in `i18n_patterns` with `hreflang` links | ADVISORY |

---

### Report format

```
Public pages:
  index    /           home.html
  about    /about/     about.html
  post     /posts/<slug>/  posts/post_detail.html
  ...

VIOLATION (crawlers cannot index this correctly — fix before relying on search):
  [robots] my_app/views.py:51 — /posts/ prefix not allowed; post detail pages are hidden
    Fix: add "Allow: /posts/" before "Disallow: /"
  [htmx] templates/posts/post_detail.html:12 — post body loads with hx-trigger="load"
    Fix: render the body in the first response; keep hx-trigger for comments
  ...

WARNING (likely issue; verify manually):
  [meta] templates/posts/post_detail.html — renders the shared site description
  [canonical] templates/posts/post_list.html — ?sort= variants have no canonical link
  ...

ADVISORY (worth doing if search traffic matters):
  [sitemap] posts app has public detail pages and no sitemap
  [og] templates/posts/post_detail.html — no Open Graph tags
  ...

OK:
  robots.txt allows every public page
  Every public page sets its own title
  ...
```

After listing all findings, print a one-line summary:

```
X violations · Y warnings · Z advisory
```

If there are VIOLATION findings, recommend fixing them before relying on search
traffic and offer to fix each one, following `docs/seo.md`. Wait for the user to
confirm before making any changes.
